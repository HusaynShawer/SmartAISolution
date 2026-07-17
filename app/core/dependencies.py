# from jose import jwt,JWTError
# import logging
# from fastapi import Depends,HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
# from sqlalchemy.ext.asyncio import AsyncSession
# from database.session import get_db
# from models.user import User
# from .config import settings
# from repositories.user_repo import UserRepository

# logger = logging.getLogger(__name__)
# outh_shcema = OAuth2PasswordBearer(tokenUrl="/auth/login")

# async def get_current_user(token:str=Depends(outh_shcema)
#                         , db:AsyncSession=Depends(get_db)):
    
#     payload = jwt.decode(token,settings.JWT_SERCERT,
#                         algorithm=[settings.JWT_ALGORTHIM])
    
#     if payload is None:
#         logger.error("INVALID ACCESS TOKEN FROM DENDENDENICES")
#         raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail="invalid or expire token")
#     user_id = payload.get("sub")
    
#     if not user_id or user_id is None:
#         raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail="USER ID NOT FOUND")
    
#     user_repo = UserRepository(db)
#     user = await user_repo.get_by_id(user_id=user_id)
    
#     if user is None:
#         logger.error("USER NOT FOUND")
#         raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail="USER NOT FOUND")
#     logger.info("user authenticated")
#     return 

from jose import jwt, JWTError
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials 
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_db
from models.user import User
from .config import settings
from repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

# استبدال OAuth2PasswordBearer بـ HTTPBearer
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SERCERT, 
            algorithms=[settings.JWT_ALGORTHIM]
        )
    except JWTError:
        logger.warning("INVALID ACCESS TOKEN FROM DEPENDENCIES")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="invalid or expired token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="USER ID NOT FOUND"
        )
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id=user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="USER NOT FOUND"
        )
        
    logger.warning("user authenticated")
    return user