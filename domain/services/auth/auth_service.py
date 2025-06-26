from domain.schemas import UserLogin, Token
from infra.repositories import UserCRUD
from utils import verify_password
from .jwt_service import JWTHandler
from domain import exeptions


async def login_user(
        auth_user: UserLogin,
        server_user: UserCRUD,
        jwt_handler: JWTHandler
) -> Token:
    user = await server_user.get_user_by_email(auth_user.email)
    if user is None:
        user = await server_user.get_user_by_username(auth_user.username)
        if user is None:
            raise exeptions.UnauthorizedException("Invalid login credentials")

    if await verify_password(auth_user.password, user.password_hash):
        token = jwt_handler.create_jwt(user.id)
        return Token(access_token=token, token_type="Bearer")
    raise exeptions.UnauthorizedException("Invalid password")


async def login_swagger(
        username: str,
        password: str,
        jwt_handler: JWTHandler,
        server_user: UserCRUD,
) -> Token:
    user = await server_user.get_user_by_username(username)
    if user is None:
        raise exeptions.UnauthorizedException("Invalid login credentials")
    if await verify_password(password, user.password_hash):
        token = jwt_handler.create_jwt(user.id)
        return Token(access_token=token, token_type="Bearer")
    raise exeptions.UnauthorizedException("Invalid password")