"""
logger.py
Centralized logging module
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Create data/logs directory
log_dir = Path("data/logs")
log_dir.mkdir(parents=True, exist_ok=True)

class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[94m",    # Blue
        logging.INFO: "\033[92m",     # Green
        logging.WARNING: "\033[93m",  # Yellow
        logging.ERROR: "\033[91m",    # Red
        logging.CRITICAL: "\033[91m", # Red
    }
    RESET = "\033[0m"

    def format(self, record):
        log_color = self.COLORS.get(record.levelno, self.RESET)
        record.levelname_colored = f"{log_color}{record.levelname}{self.RESET}"
        fmt = f"[%(asctime)s] [{record.levelname_colored}] [%(name)s] %(message)s"
        formatter = logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # File Handler
        file_handler = RotatingFileHandler(
            log_dir / "server.log", maxBytes=10*1024*1024, backupCount=5
        )
        file_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ColorFormatter())
        logger.addHandler(console_handler)
        
    return logger
