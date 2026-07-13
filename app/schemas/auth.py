from pydantic import BaseModel,EmailStr

class UserRegisterRequest(BaseModel):
    email:EmailStr
    password:str
    full_name:str
    
class UserLoginRequest(BaseModel):
    email:EmailStr
    passwrod:str
    
class TokenResponse(BaseModel):
    access_token:str
    token_type:str="bearer"
    
class UserRespone(BaseModel):
    id:str
    full_naame:str
    role:str
    
    model_config = {"from_attributes":True}