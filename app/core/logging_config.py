import logging
import os
from logging.handlers import RotatingFileHandler
from core.config import settings

def setup_logging():
    os.makedirs("logs",exist_ok=True)
    logging.basicConfig(
        level=getattr(
            logging,settings.LOG_LEVEL.upper(),logging.INFO),
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            handlers=[
                logging.StreamHandler(),
                RotatingFileHandler(
                    "logs/app.log",
                    maxBytes=5*1024*1024,
                    backupCount=5,
                    encoding="utf-8"
                )
            ] 
        
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)