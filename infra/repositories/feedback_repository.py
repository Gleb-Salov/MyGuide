from domain.schemas import Feedback, FeedbackRead
from sqlalchemy.ext.asyncio import AsyncSession
from domain.models import UserEventFeedback, User
from sqlalchemy import select, and_
from typing import Optional
from uuid import UUID


class FeedbackCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_feedback(self, user_id: UUID, event_id: UUID) -> Optional[UserEventFeedback]:
        smtm = select(UserEventFeedback).where(and_(UserEventFeedback.user_id == user_id, UserEventFeedback.event_id == event_id))
        result = await self.session.execute(smtm)
        return result.unique().scalars().one_or_none()

    async def feedback_an_event(self, feedback: Feedback, user: User) -> Optional[FeedbackRead]:
        existing_feedback = await self.get_feedback(user.id, feedback.event_id)
        if existing_feedback:
            if existing_feedback.like == feedback.feedback:
                await self.session.delete(existing_feedback)
                await self.session.commit()
                return None
            else:
                existing_feedback.like = feedback.feedback
                await self.session.commit()
                return FeedbackRead.model_validate(existing_feedback)

        new_feedback = UserEventFeedback(
            event_id=feedback.event_id,
            user_id=user.id,
            like=feedback.feedback
        )
        self.session.add(new_feedback)
        await self.session.commit()
        await self.session.refresh(new_feedback)
        return FeedbackRead.model_validate(new_feedback)

