from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from .users import InterestRead


class EventDateLocationRead(BaseModel):
    date: datetime
    location: str = Field(min_length=1, max_length=300)

    model_config = ConfigDict(from_attributes=True)


class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: Optional[str] = Field(default=None)
    date_locations: List[EventDateLocationRead]
    interests: List[str] = Field(default_factory=list)


class EventRead(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    date_locations: List[EventDateLocationRead]
    interests: List[InterestRead]

    model_config = ConfigDict(from_attributes=True)