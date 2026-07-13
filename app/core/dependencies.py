from jose import jwt,JWTError
import logging
from fastapi import Depends,HTTPExeption, status
from fastapi.securit import OAuth2PasswodBearer
from sqlalchemyy.ext.asyncio import AsyncSession
from database.session import get_db
from models.user import User
from core.Config import settings
from repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)
outh_shcema = OAuth2PasswodBearer(tokenUrl="/auth/login")
async def get_current_user(token:str=Depends(outh_shcema)
                        , db:AsyncSession=Depends(get_db)):
    
    payload = jwt.decode(token,settings.JWT_SERCERT,
                        algorithm=[settings.JWT_ALGORTHIM])
    
    if payload is None:
        logger.warning("INVALID ACCESS TOKEN FROM DENDENDENICES")
        raise HTTPExeption(status_code = status.HTTP_401_UNAUTHORIZED,detail="invalid or expire token")
    user_id = payload.get("sub")
    
    if not user_id or user_id is None:
        raise HTTPExeption(status_code = status.HTTP_401_UNAUTHORIZED,detail="USER ID NOT FOUND")
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id=user_id)
    
    if user is None:
        raise HTTPExeption(status_code = status.HTTP_401_UNAUTHORIZED,detail="USER NOT FOUND")
    logger.warning("user authenticated")
    return user