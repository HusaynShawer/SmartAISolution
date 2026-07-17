from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_db
from services.auth_service import AuthSerivce
from schemas.auth import UserRegisterRequest, UserLoginRequest
import logging

logger = logging.Logger(__name__)
api_router = APIRouter(prefix="/auth",tags=["Auth"])

@api_router.post("/register")
async def register(request:UserRegisterRequest,db:AsyncSession=Depends(get_db)):
    service = AuthSerivce(db)
    logger.info(("user register now fuck it "))
    return await service.register(
        email=request.email,
        password=request.password,
        full_name=request.full_name
    )
    
@api_router.post("/login")
async def register(request:UserLoginRequest,db:AsyncSession=Depends(get_db)):
    service = AuthSerivce(db)
    return await service.login(
        email=request.email,
        password=request.password)
    