from api import users_router, auth_router, events_router
from fastapi import FastAPI


app = FastAPI(title="MyGuide API")

app.include_router(users_router)
app.include_router(auth_router)
app.include_router(events_router)