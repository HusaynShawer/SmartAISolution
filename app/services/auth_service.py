from fastapi import HTTPException,status
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.user_repo import UserRepository
from core.security import hash_password,verfiy_password,create_access_token
from schemas.auth import TokenResponse

class AuthSerivce:
    def __init__(self,session:AsyncSession):
        self.user_repo = UserRepository(session=session)
        
    async def register(self,email:str,password:str,full_name:str)->TokenResponse:
        
        existing_user = await self.user_repo.get_by_email(email)
        
        if existing_user:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "email already exist"
            )
        hashed = hash_password(password=password)
        user = await self.user_repo.create_user(email=email,hashed_password=hashed,full_name=full_name)
        token = create_access_token(data={"sub":user.id,"email":user.email})
        return TokenResponse(access_token=token)
    
    async def login(self,email:str,password:str)->TokenResponse:
        user = await self.user_repo.get_by_email(email=email)
        if not user or not verfiy_password(plain_password=password,hash_password=user.hashed_password):
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "wrong password or email"
            )
        token = create_access_token(data={"sub":user.id,"email":user.email})
        return TokenResponse(access_token=token)