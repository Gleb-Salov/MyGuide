from domain.schemas import UserCreate, UserRead
from fastapi import APIRouter, Depends, status
from infra.repositories import UserCRUD
from infra.deps import get_user_crud


router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    user_crud: UserCRUD = Depends(get_user_crud),
) -> UserRead:
    return await user_crud.create_user(user)