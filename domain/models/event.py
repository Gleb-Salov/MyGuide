from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime, Table, Column, UniqueConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.expression import true
from infra.db.base import Base
from datetime import datetime
from uuid import uuid4


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (UniqueConstraint("title", "description_hash", name="uq_event_title_description_hash"),)

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    description_hash: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())

    date_locations: Mapped[list["EventDateLocation"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    interests: Mapped[list["Interest"]] = relationship( # type: ignore
        "Interest",
        secondary="event_interest_association",
        back_populates="events",
        lazy="selectin"
    )

    feedback: Mapped[list["UserEventFeedback"]] = relationship(
        back_populates="event",
    )

    def __repr__(self):
        return f"<Event id={self.id} title='{self.title}'>"


class EventDateLocation(Base):
    __tablename__ = "event_date_locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("events.id"), nullable=False)

    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    location: Mapped[str] = mapped_column(String(300), nullable=False)

    event: Mapped["Event"] = relationship(
        back_populates="date_locations",
    )


class UserEventFeedback(Base):
    __tablename__ = "user_event_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    event_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True)
    like: Mapped[bool] = mapped_column(Boolean, nullable=True)

    user = relationship("User", back_populates="feedback")
    event = relationship("Event", back_populates="feedback")

    def __repr__(self):
        return f"<Feedback user_id={self.user_id} event_id={self.event_id} like={self.like}>"


event_interest_association  = Table(
    "event_interest_association",
    Base.metadata,
    Column("event_id", ForeignKey("events.id"), primary_key=True),
    Column("interest_id", ForeignKey("interests.id"), primary_key=True),
)