from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from infra.db.base import Base
from datetime import datetime
from uuid import uuid4


class Event(Base):
    __tablename__ = "events"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(String(1000))
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    location: Mapped[str] = mapped_column(String(300), nullable=False)
    # attribute jr teg for interests

    feedback: Mapped[list["UserEventFeedback"]] = relationship(
        back_populates="event",
    )

    def __repr__(self):
        return f"<Event id={self.id} title='{self.title}'>"


class UserEventFeedback(Base):
    __tablename__ = "user_event_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id"), nullable=False, index=True)
    like: Mapped[bool] = mapped_column(Boolean)

    user = relationship("User", back_populates="feedback")
    event = relationship("Event", back_populates="feedback")

    def __repr__(self):
        return f"<Feedback user_id={self.user_id} event_id={self.event_id} like={self.like}>"