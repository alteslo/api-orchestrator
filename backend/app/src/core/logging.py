import os
import sys

from app.configs.settings import settings
from loguru import logger as loguru_logger

LOG_PATH = os.path.join(
    settings.LOG_PATH, f"log_{settings.FILES_PROJECT_NAME.lower()}.log"
)

loguru_logger.remove()
logger = loguru_logger.bind(name="general_logger")

logger.add(
    sink=LOG_PATH,
    format="{time} {level} {message}",
    level="DEBUG",  # settings.LOG_LEVEL,
    rotation="50 MB",
)  # retention="5 days")  #, compression="zip")  # , rotation="500 KB)"
logger.add(sys.stderr, level=settings.LOG_LEVEL)

logger.debug(f"Service {settings.FILES_PROJECT_NAME} start logging to {LOG_PATH}")
