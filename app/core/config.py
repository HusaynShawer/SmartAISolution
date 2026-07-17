from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL:str
    
    JWT_SERCERT:str
    JWT_ALGORTHIM: str
    JWT_EXPIRATION_MIN:int

    #RAG
    CHUNK_SIZE:int
    CHUNK_OVERLAB:int
    MAX_FILE_SIZE:int
    COHERE_API_KEY:str
    EMBEDDING_MODEL:str

    #APP
    LOG_LEVEL:str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
settings = Settings()