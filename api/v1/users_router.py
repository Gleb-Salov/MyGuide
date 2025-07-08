from domain.schemas import UserCreate, UserRead, InterestAdd, Feedback, FeedbackRead
from fastapi import APIRouter, Depends, status, Response
from infra.repositories import UserCRUD, FeedbackCRUD
from infra.deps import get_user_crud, get_current_user, get_feedback_crud
from domain.models import User
from typing import Union


router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    user_crud: UserCRUD = Depends(get_user_crud),
) -> UserRead:
    return await user_crud.create_user(user)

@router.post("/interests", response_model=UserRead, status_code=status.HTTP_200_OK)
async def add_interest(
    interest: InterestAdd,
    user: User = Depends(get_current_user),
    user_crud: UserCRUD = Depends(get_user_crud),
) -> UserRead:
    return await user_crud.add_interests(user, interest)

@router.post("/events/feedback", response_model=FeedbackRead, status_code=status.HTTP_200_OK)
async def add_feedback(
        feedback: Feedback,
        user: User = Depends(get_current_user),
        feedback_crud: FeedbackCRUD = Depends(get_feedback_crud),
) -> Union[FeedbackRead, Response]:
    result = await feedback_crud.feedback_an_event(feedback, user)
    if result is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return result