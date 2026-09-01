import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import create_access_token, hash_password, verify_password
from repositories.user_repo import UserRepository
from schemas.auth import TokenResponse


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.user_repo = UserRepository(session=session)
        self.logger = logging.getLogger(__name__)

    async def register(
        self, email: str, password: str, full_name: str
    ) -> TokenResponse:
        self.logger.info("Attempting to register user: %s", email)
        existing_user = await self.user_repo.get_by_email(email)

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="email already exists",
            )

        hashed = hash_password(password=password)
        user = await self.user_repo.create_user(
            email=email, hashed_password=hashed, full_name=full_name
        )
        token = create_access_token(data={"sub": user.id, "email": user.email})
        self.logger.info("User registered successfully: %s", user.email)
        return TokenResponse(access_token=token)

    async def login(self, email: str, password: str) -> TokenResponse:
        self.logger.info("Login attempt for user: %s", email)
        user = await self.user_repo.get_by_email(email=email)
        if not user or not verify_password(
            plain_password=password, hashed_password=user.hashed_password
        ):
            self.logger.warning("Failed login attempt for user: %s", email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="wrong password or email",
            )
        token = create_access_token(data={"sub": user.id, "email": user.email})
        self.logger.info("User logged in successfully: %s", user.email)
        return TokenResponse(access_token=token)
