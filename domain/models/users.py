from sqlalchemy import Integer, String, Table, Column, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from infra.db.base import Base
from datetime import datetime
from uuid import uuid4


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    create_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    interests: Mapped[list["Interest"]] = relationship(
        "Interest",
        secondary="user_interest_association",
        back_populates="users",
        lazy="joined",
    )

    feedback: Mapped[list["UserEventFeedback"]] = relationship( # type: ignore
        back_populates="user",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


class Interest(Base):
    __tablename__ = "interests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    users: Mapped[list[User]] = relationship(
        "User",
        secondary="user_interest_association",
        back_populates="interests",
    )


user_interest_association = Table(
    "user_interest_association",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("interest_id", ForeignKey("interests.id"), primary_key=True),
)