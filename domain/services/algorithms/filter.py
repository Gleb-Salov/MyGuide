from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from domain.models import User, Event, Interest, UserEventFeedback, EventDateLocation
from domain.schemas import EventRead
from typing import Optional, List
from datetime import datetime, timedelta


class FilterAlgorithm:
    def __init__(self, session: AsyncSession, user: User):
        self.session = session
        self.user = user

    async def filter(self, limit: int = 10) -> List[EventRead]:
        now = datetime.now()

        user = await self._get_linked_user()
        seen_event_ids = await self._get_seen_event_ids(user)
        user_interest_ids = await self._get_all_interest_ids(user)
        liked_ids, disliked_ids = await self._get_feedback_interest_ids(user)

        candidate_events = await self._get_candidate_events(user_interest_ids, seen_event_ids, now)
        scored_events = self._score_events(candidate_events, user_interest_ids, liked_ids, disliked_ids, now)

        top_n = sorted(scored_events, key=lambda x: x["score"], reverse=True)[:limit]
        recommended_events = [e["event"] for e in top_n]
        return list(EventRead.model_validate(event) for event in recommended_events)

    async def _get_linked_user(self) -> User:
        smtm = select(User).where(User.id == self.user.id).options(
            selectinload(User.interests)
        )
        result = await self.session.execute(smtm)
        return result.unique().scalar_one()

    async def _get_seen_event_ids(self, user: User) -> set[int]:
        stmt = select(UserEventFeedback.event_id).where(UserEventFeedback.user_id == user.id)
        result = await self.session.execute(stmt)
        return {row[0] for row in result}

    async def _get_all_interest_ids(self, user: User) -> set[int]:
        ids = {i.id for i in user.interests}
        for interest in user.interests:
            await self.session.refresh(interest, attribute_names=["children"]) # type: ignore
            ids.update(child.id for child in interest.children) # type: ignore
        return ids

    async def _get_feedback_interest_ids(self, user: User) -> tuple[set[int], set[int]]:
        stmt = select(UserEventFeedback).where(UserEventFeedback.user_id == user.id)
        result = await self.session.execute(stmt)
        feedbacks = result.scalars().all()

        liked_event_ids = {f.event_id for f in feedbacks if f.like}
        disliked_event_ids = {f.event_id for f in feedbacks if not f.like}

        stmt2 = (
            select(Event.id, Interest.id)
            .join(Event.interests)
            .where(Event.id.in_(liked_event_ids | disliked_event_ids))
        )
        result2 = await self.session.execute(stmt2)

        liked, disliked = set(), set()
        for event_id, interest_id in result2:
            if event_id in liked_event_ids:
                liked.add(interest_id)
            elif event_id in disliked_event_ids:
                disliked.add(interest_id)
        return liked, disliked

    async def _get_linked_events(self, user: User) -> Optional[List[Event]]:
        smtm = select(Event).where(Event.feedback == user.feedback).options(
            selectinload(Event.feedback),
        )
        result = await self.session.execute(smtm)
        return list(result.scalars().all())

    async def _get_candidate_events(self, interest_ids: set[int], exclude_ids: set, now: datetime) -> List[Event]:
        date_limit = now + timedelta(days=7)

        stmt = (
            select(Event)
            .where(
                Event.is_active == True,
                ~Event.id.in_(exclude_ids),
                Event.date_locations.any(EventDateLocation.date >= now),
                Event.date_locations.any(EventDateLocation.date <= date_limit),
                Event.interests.any(Interest.id.in_(interest_ids)),
            )
            .options(
                selectinload(Event.date_locations),
                selectinload(Event.interests),
            )
            .distinct()
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def _score_events(
            events: List[Event],
            user_interest_ids: set[int],
            liked_interest_ids: set[int],
            disliked_interest_ids: set[int],
            now: datetime,
    ) -> List[dict]:
        scored = []

        for event in events:
            score = 0
            event_interest_ids = {i.id for i in event.interests}
            match_count = len(event_interest_ids & user_interest_ids)
            score += match_count * 3

            closest_date = min((d.date for d in event.date_locations if d.date >= now), default=None)
            if closest_date:
                delta_h = (closest_date - now).total_seconds() / 3600
                if delta_h < 1:
                    score -= 2
                elif 1 <= delta_h <= 3:
                    score += 3
                elif 3 < delta_h <= 24:
                    score += 1

            if event_interest_ids & liked_interest_ids:
                score += 2
            if event_interest_ids & disliked_interest_ids:
                score -= 3

            scored.append({"event": event, "score": score})
        return scored