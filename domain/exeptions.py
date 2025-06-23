from fastapi import HTTPException
from typing import Optional


class AppException(HTTPException):
    def __init__(self, status_code: int, detail: Optional[str] = None, headers: Optional[dict] = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class BadRequestException(AppException):
    def __init__(self, detail: Optional[str] = "Bad request"):
        super().__init__(400, detail)


class NotFoundException(AppException):
    def __init__(self, detail: Optional[str] = "Resource not found"):
        super().__init__(404, detail)


class ConflictException(AppException):
    def __init__(self, detail: Optional[str] = "Conflict detected"):
        super().__init__(409, detail)


class UnauthorizedException(AppException):
    def __init__(self, detail: Optional[str] = "Unauthorized"):
        super().__init__(
            401,
            detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class InternalServerErrorException(AppException):
    def __init__(self, detail: Optional[str] = "Internal server error"):
        super().__init__(500, detail)
