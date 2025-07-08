from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from infra.repositories import EventCRUD
from domain.models import User
from domain.schemas import EventCreate, EventRead
from domain.services.algorithms import FilterAlgorithm
from infra.deps import get_event_crud, get_current_user
from typing import List
from infra.deps.database import get_async_session


router = APIRouter(prefix="/event", tags=["events"])

@router.get("/recommendations", response_model=List[EventRead], status_code=status.HTTP_200_OK)
async def get_recommendations(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> List[EventRead]:
    rec = FilterAlgorithm(session, user)
    return await rec.filter()


@router.post("/", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def create_event(
    event: EventCreate,
    event_crud: EventCRUD = Depends(get_event_crud),
) -> EventRead:
    return await event_crud.event_create(event)

@router.post("/pars", response_model=List[EventRead], status_code=status.HTTP_201_CREATED)
async def create_events_from_parser(
    event_crud: EventCRUD = Depends(get_event_crud)
) -> List[EventRead]:
    await event_crud.add_events_from_parser()
    return await event_crud.get_all_events()

@router.delete("/", response_model=List[EventRead], status_code=status.HTTP_200_OK)
async def delete_invalid_events(
        event_crud: EventCRUD = Depends(get_event_crud)
)-> List[EventRead]:
    deleted_events = await event_crud.delete_invalid_events()
    return deleted_events


if __name__ == "__main__":
    async def main():
        async for session in get_async_session():
            event_crud = EventCRUD(session=session)
            await event_crud.add_events_from_parser()

    import asyncio
    asyncio.run(main())