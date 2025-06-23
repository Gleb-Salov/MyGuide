from domain.schemas import UserCreate, UserRead
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from domain.models.users import User
from utils import hash_password
from sqlalchemy import select
from pydantic import EmailStr
from domain import exeptions
from typing import Optional
from uuid import UUID


class UserCRUD:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_email(self, email: EmailStr) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def create_user(self, user: UserCreate) -> UserRead:
        existing_user = await self.get_user_by_email(user.email)

        if existing_user:
            raise exeptions.BadRequestException("User with this email already exists")

        new_user = User(
            username=user.username,
            email=user.email,
            password_hash=await hash_password(user.password)
        )

        self.session.add(new_user)
        try:
            await self.session.commit()
            await self.session.refresh(new_user)
        except IntegrityError:
            await self.session.rollback()
            raise exeptions.BadRequestException("User already exists")
        except Exception:
            await self.session.rollback()
            raise exeptions.InternalServerErrorException()

        return UserRead.model_validate(new_user)