import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.rate_limit import limiter
from database.session import get_db
from schemas.auth import UserLoginRequest, UserRegisterRequest
from services.auth_service import AuthService

logger = logging.getLogger(__name__)

api_router = APIRouter(prefix="/auth", tags=["Auth"])


@api_router.post("/register")
@limiter.limit(settings.DEFAULT_RATE_LIMIT)
async def register(
    request: Request,
    user_request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    logger.info("Register request received for: %s", user_request.email)
    return await service.register(
        email=user_request.email,
        password=user_request.password,
        full_name=user_request.full_name,
    )


@api_router.post("/login")
@limiter.limit(settings.DEFAULT_RATE_LIMIT)
async def login(
    request: Request,
    user_request: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.login(
        email=user_request.email, password=user_request.password
    )
