from datetime import datetime, timedelta, timezone
from sqlalchemy.dialects.postgresql import UUID
from infra.config.app_settings import settings
from functools import lru_cache
from jose import jwt, JWTError
from typing import Optional
import os


class JWTHandler:
    def __init__(self, private_key_path: Optional[str] = settings.JWT_PRIVATE_KEY_PATH,
                 public_key_path: Optional[str] = settings.JWT_PUBLIC_KEY_PATH,
                 algorithm: str = "RS256",
                 expire_minutes: int = 60):
        self.algorithm = algorithm
        self.expire_minutes = expire_minutes

        if private_key_path is None:
            raise ValueError("Private key path is not set")

        if public_key_path is None:
            raise ValueError("JWT_PUBLIC_KEY_PATH is not set")

        if not os.path.exists(private_key_path):
            raise FileNotFoundError(f"Private key file not found: {private_key_path}")
        with open(private_key_path, "r", encoding="utf-8") as f:
            self._private_key = f.read()

        if not os.path.exists(public_key_path):
            raise FileNotFoundError(f"Public key file not found: {public_key_path}")
        with open(public_key_path, "r", encoding="utf-8") as f:
            self._public_key = f.read()


    def create_jwt(self, user_id: UUID) -> str:
        headers = {"alg": self.algorithm,
                   "typ": "JWT"}
        payload = {
            "sub": str(user_id),
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=self.expire_minutes),
        }
        return jwt.encode(payload, self._private_key, algorithm=self.algorithm, headers=headers)

    def decode_jwt(self, token: str) -> dict:
        try:
            return jwt.decode(token, self._public_key, algorithms=[self.algorithm])
        except JWTError as e:
            raise JWTError(f"Invalid token: {str(e)}")


@lru_cache
def get_jwt_handler() -> JWTHandler:
    return JWTHandler()