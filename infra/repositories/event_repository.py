from typing import List, Optional
from domain.schemas import EventCreate, EventRead
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from domain.models import Interest, Event, EventDateLocation
from sqlalchemy import select, func, and_
from domain import exeptions
from datetime import datetime
from domain.services.afisha import EventParser
import hashlib


class EventCRUD:
    def __init__(self, session: AsyncSession, event_parser: Optional[EventParser] = None):
        self.session = session
        self.event_parser = event_parser or EventParser()

    async def event_create(self, event: EventCreate) -> EventRead:
        interests = await self._get_interests_by_names(event.interests)
        new_event = Event(
            title=event.title,
            description=event.description,
            interests=interests,
        )
        for dl in event.date_locations:
            new_event.date_locations.append(
                EventDateLocation(date=dl.date, location=dl.location)
            )
        self.session.add(new_event)

        try:
            await self.session.commit()
            await self.session.refresh(new_event)
        except Exception:
            await self.session.rollback()
            raise exeptions.InternalServerErrorException("Something went wrong")

        return EventRead.model_validate(new_event)

    async def delete_invalid_events(self) -> List[EventRead]:
        now = datetime.now()
        deleted_events = []
        async with self.session.begin():
            stmt = select(Event).options(selectinload(Event.date_locations), selectinload(Event.feedback))
            result = await self.session.execute(stmt)
            events = result.scalars().all()
            for event in events:

                event.date_locations[:] = [dl for dl in event.date_locations if dl.date >= now]
                event.is_active = bool(event.date_locations)
                if not event.is_active and not event.feedback:
                    deleted_events.append(event)
                    await self.session.delete(event)
        return list(EventRead.model_validate(deleted_event) for deleted_event in deleted_events)

    async def get_all_events(self) -> List[EventRead]:
        stmt = select(Event).options(selectinload(Event.date_locations), selectinload(Event.interests))
        result = await self.session.execute(stmt)
        events = result.scalars().all()

        return list(EventRead.model_validate(event) for event in events)

    async def add_events_from_parser(self) -> None:
        new_events = await self.event_parser.parse()

        async with self.session.begin():
            for event_data in new_events:
                await self._add_or_update_event(event_data)

    @staticmethod
    def get_description_hash(description: str) -> str:
        return hashlib.md5(description.encode('utf-8')).hexdigest()

    async def _add_or_update_event(self, event_data: dict) -> None:
        title = event_data['title']
        description = event_data.get('description') or ""
        description_hash = self.get_description_hash(description)
        date_locations = event_data.get('date_locations', [])
        interest_names = event_data.get('interests', [])

        existing_event = await self._get_event_by_title_description_hash(title, description_hash)

        if not existing_event and description != "":
            existing_event = await self._get_event_by_title(title)

        if existing_event:
            await self._update_event_dates(existing_event, date_locations)

            if existing_event.description != description:
                existing_event.description = description
                existing_event.description_hash = description_hash

            if interest_names:
                parent_interest = await self._get_or_create_parent_interest()
                child_interests = await self._get_or_create_child_interests(interest_names, parent_interest)
                interests_set = set(existing_event.interests)

                for interest in child_interests:
                    if interest not in interests_set:
                        existing_event.interests.append(interest)

                if parent_interest not in existing_event.interests:
                    existing_event.interests.append(parent_interest)
            await self.session.flush()

        else:

            new_event = Event(title=title, description=description, description_hash=description_hash)
            for dl in date_locations:
                new_event.date_locations.append(
                    EventDateLocation(date=dl['date'], location=dl['location'])
                )
            if interest_names:
                parent_interest = await self._get_or_create_parent_interest()
                child_interests = await self._get_or_create_child_interests(interest_names, parent_interest)
                new_event.interests.extend(child_interests)
                if parent_interest not in new_event.interests:
                    new_event.interests.append(parent_interest)
            self.session.add(new_event)
            await self.session.flush()

    async def _get_event_by_title_description_hash(self, title: str, description_hash: str) -> Optional[Event]:
        stmt = select(Event).where(
            and_(Event.title == title, Event.description_hash == description_hash)
        ).options(
            selectinload(Event.date_locations),
            selectinload(Event.interests)
        )
        result = await self.session.execute(stmt)
        return result.scalars().one_or_none()

    async def _get_event_by_title(self, title: str) -> Optional[Event]:
        stmt = select(Event).where(Event.title == title).options(selectinload(Event.date_locations),
                                                                 selectinload(Event.interests))
        result = await self.session.execute(stmt)
        return result.scalars().one_or_none()

    async def _update_event_dates(self, event: Event, new_dates: List[dict]) -> None:
        existing_dates = {(date_locations.date, date_locations.location) for date_locations in event.date_locations}
        new_data_added = False
        for date_location in new_dates:
            key = (date_location['date'], date_location['location'])
            if key not in existing_dates:
                new_date_location = EventDateLocation(
                    date=date_location['date'],
                    location=date_location['location'],
                    event=event
                )
                self.session.add(new_date_location)
                new_data_added = True
        if new_data_added:
            event.is_active = True
        await self.session.flush()

    async def _get_interests_by_names(self, names: List[str]) -> List[Interest]:
        if not names:
            return []
        lower_names = [name.lower() for name in names]
        stmt = select(Interest).where(func.lower(Interest.name).in_(lower_names))
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def _get_or_create_parent_interest(self) -> Interest:
        parent_name = self.event_parser.get_parent_name_from_url()
        stmt = select(Interest).where(Interest.name == parent_name)
        result = await self.session.execute(stmt)
        parent_interest = result.scalars().one_or_none()
        if not parent_interest:
            parent_interest = Interest(name=parent_name)
            self.session.add(parent_interest)
        await self.session.flush()
        return parent_interest

    async def _get_or_create_child_interests(self, names: List[str], parent: Interest) -> List[Interest]:
        if not names:
            return []
        stmt = select(Interest).where(Interest.name.in_(names), Interest.parent_id == parent.id)
        result = await self.session.execute(stmt)
        existing = {i.name: i for i in result.scalars().all()}

        interests = []
        for name in names:
            interest = existing.get(name)
            if not interest:
                interest = Interest(name=name, parent=parent)
                self.session.add(interest)
            interests.append(interest)
        await self.session.flush()
        return interests
