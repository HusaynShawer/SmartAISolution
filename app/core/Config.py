from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL:str
    
    JWT_SERCERT = ...
    JWT_ALGORTHIM = STR
    JWT_EXPIRATION_MIN=int

    #RAG
    CHUNK_SIZE = int
    CHUNK_OVERLAB = int
    MAX_FILE_SIZE=int

    #APP
    LOG_LEVEL:str = 'INFO'
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
settings = settings()