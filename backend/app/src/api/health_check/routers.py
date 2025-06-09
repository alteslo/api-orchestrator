from fastapi import APIRouter

from app.configs.settings import get_settings
from app.src.api.health_check.services import check_service_health
from fastapi import Request
from app.src.core.logging import logger


router = APIRouter()
config = get_settings()


@router.get("/")
async def health_check(request: Request):
    # client_host = request.client.host
    # logger.info(f'health_check client_host: {client_host}')
    await check_service_health()
    info = {
        "service": config.FILES_PROJECT_NAME,
        "version": config.FILES_VERSION,
        "debug": config.DEBUG
    }
    return info
