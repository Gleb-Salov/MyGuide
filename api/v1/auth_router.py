from domain.services.auth.jwt_service import get_jwt_handler, JWTHandler
from fastapi import APIRouter, Depends, status, Form
from domain.services.auth import login_user, login_swagger
from infra.repositories import UserCRUD
from domain.schemas import UserLogin
from infra.deps import get_user_crud
from domain.schemas import Token


router = APIRouter(prefix="/auth", tags=["users"])

@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def auth_user(
    user: UserLogin,
    server_user: UserCRUD = Depends(get_user_crud),
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
) -> Token:
    token = await login_user(user,server_user,jwt_handler)
    return token

# router for tests on swagger
@router.post("/login-swagger", response_model=Token, status_code=status.HTTP_200_OK)
async def auth_user_swagger(
        username: str = Form(...),
        password: str = Form(...),
        server_user: UserCRUD = Depends(get_user_crud),
        jwt_handler: JWTHandler = Depends(get_jwt_handler)
) -> Token:
    token = await login_swagger(username,password,jwt_handler,server_user)
    return token
