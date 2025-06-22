from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_async_session
from infra.repositories import UserCRUD
from typing import Type, Callable, Any
from fastapi import Depends


def get_crud(crud_class: Type) -> Callable[..., Any]:
    async def dependency(session: AsyncSession = Depends(get_async_session)):
        return crud_class(session)
    return dependency

get_user_crud = get_crud(UserCRUD)