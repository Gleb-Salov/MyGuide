from pydantic import BaseModel, ConfigDict,  Field
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from .users import InterestRead


class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: Optional[str] = Field(default=None, min_length=1, max_length=1000)
    date: datetime
    location: str = Field(min_length=1, max_length=300)


class EventRead(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    date: datetime
    location: str
    interests: List[InterestRead]

    model_config = ConfigDict(from_attributes=True)