from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from database.base import Base
from database.session import engine
from core.logging_config import setup_logging
from contextlib import asynccontextmanager
from routers import auth, document, ticket
#SETUP LOGGER
setup_logging()

#LIFESPAIN

@asynccontextmanager

async def lifespan(app:FastAPI):
    yield
    await engine.dispose()
    
app = FastAPI(
    title = "AI Support Agent",
    version="1.0.0",
    lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


app.include_router(auth.api_router)
app.include_router(document.router)
app.include_router(ticket.router)

@app.get("/health",tags=["Health"])
async def cheak_health():
    return {"status" : "ok" , "version" : "1.0.0"}