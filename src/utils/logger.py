import logging
import sys
from src.config.paths import LOGS_DIR

def setup_logger():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("ClipForgeAI")
    logger.setLevel(logging.DEBUG)
    
    if logger.handlers:
        return

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('[%(levelname)s] %(name)s: %(message)s')
    console_handler.setFormatter(console_format)
    
    # File handler (app.log)
    file_handler = logging.FileHandler(LOGS_DIR / "app.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - [%(levelname)s] - %(name)s - %(message)s')
    file_handler.setFormatter(file_format)
    
    # Error file handler (error.log)
    error_handler = logging.FileHandler(LOGS_DIR / "error.log", encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_format)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"ClipForgeAI.{name}")