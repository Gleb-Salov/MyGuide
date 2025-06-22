from pydantic import BaseModel, ConfigDict,  Field, EmailStr, constr
from datetime import datetime
from typing import List
from uuid import UUID


class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(min_length=3, max_length=254)


class InterestRead(BaseModel):
    name: str
    id: int

    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    password: constr(min_length=8, max_length=64)


class UserRead(UserBase):
    id: UUID
    create_at: datetime
    interests: List[InterestRead]

    model_config = ConfigDict(from_attributes=True)