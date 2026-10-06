import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from core.config import settings

BASE_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = BASE_DIR / "logs"

def setup_logging():
    LOG_DIR.mkdir(parents=True,exist_ok=True)
    logging.basicConfig(
        level=getattr(
            logging,settings.LOG_LEVEL.upper(),logging.INFO),
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            handlers=[
                logging.StreamHandler(),
                RotatingFileHandler(
                    LOG_DIR / "app.log",
                    maxBytes=5*1024*1024,
                    backupCount=5,
                    encoding="utf-8"
                )
            ] 
        
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)