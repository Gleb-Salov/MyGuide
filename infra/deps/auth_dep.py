from domain.services.auth.jwt_service import JWTHandler
from fastapi.security import OAuth2PasswordBearer
from domain.services.auth import get_jwt_handler
from jose import JWTError, ExpiredSignatureError
from infra.repositories import UserCRUD
from infra.deps import get_user_crud
from pydantic import ValidationError
from domain.models import User
from domain import exeptions
from fastapi import Depends
from uuid import UUID


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(
        token: str = Depends(oauth2_scheme),
        user: UserCRUD = Depends(get_user_crud),
        jwt_handler: JWTHandler = Depends(get_jwt_handler),
        ) -> User:

    try:
        payload = jwt_handler.decode_jwt(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise exeptions.UnauthorizedException("Invalid token: no subject")
        user_uuid = UUID(user_id)

    except ExpiredSignatureError:
        raise exeptions.UnauthorizedException("Token has expired")

    except (JWTError, ValidationError, ValueError):
        raise exeptions.UnauthorizedException("Invalid authentication credentials")

    current_user = await user.get_user_by_id(user_uuid)
    if current_user is None:
        raise exeptions.NotFoundException("User not found")

    return current_user