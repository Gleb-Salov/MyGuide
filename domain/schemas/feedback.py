from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class Feedback(BaseModel):
    event_id: UUID
    feedback: bool


class FeedbackRead(Feedback):
    user_id: UUID
    feedback: bool = Field(..., alias="like")

    model_config = ConfigDict(from_attributes=True)
