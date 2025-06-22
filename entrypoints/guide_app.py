from api import users_router
from fastapi import FastAPI


app = FastAPI(title="MyGuide API")

app.include_router(users_router)
