from domain.schemas import UserCreate, UserRead, InterestAdd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from domain.models.users import User, Interest
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

    async def get_user_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_user_with_interests(self, user_id: UUID) -> Optional[User]:
        stmt = select(User).options(selectinload(User.interests)).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_interest_by_name(self, interest_name: str) -> Optional[Interest]:
        smth = select(Interest).where(Interest.name.ilike(interest_name))
        result = await self.session.execute(smth)
        return result.unique().scalar_one_or_none()

    async def create_user(self, user: UserCreate) -> UserRead:
        existing_user_email = await self.get_user_by_email(user.email)
        existing_user_name = await self.get_user_by_username(user.username)

        if existing_user_name:
            raise exeptions.BadRequestException("User with this username already exists")

        if existing_user_email:
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

    async def add_interests(self, current_user: User, new_interest: InterestAdd) -> UserRead:
        user = await self.get_user_with_interests(current_user.id)
        interest = await self.get_interest_by_name(new_interest.name)

        if interest is None:
            raise exeptions.BadRequestException("Interest does not exist")
        if interest in user.interests:
            raise exeptions.BadRequestException("User already has this interest")

        user.interests.append(interest)
        try:
            await self.session.commit()
            await self.session.refresh(user)
        except IntegrityError:
            await self.session.rollback()
            raise exeptions.BadRequestException("User already has this interest")
        except Exception:
            await self.session.rollback()
            raise exeptions.InternalServerErrorException()
        return UserRead.model_validate(user)