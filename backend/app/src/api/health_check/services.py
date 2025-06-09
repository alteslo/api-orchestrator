from fastapi import HTTPException, status
from httpx import AsyncClient, HTTPError
from minio.error import MinioException, S3Error

from app.configs.settings import get_settings
from app.src.core.constants.constants import MAIN_SERVICE_HEALTH_CHECK_URL
from app.src.core.logging import logger
from app.src.core.session import MinIOSession

config = get_settings()


async def check_minio():
    try:
        exist = MinIOSession().client.bucket_exists(config.MINIO_BUCKET_NAME)
        if not exist:
            raise S3Error(code=status.HTTP_404_NOT_FOUND, message='Bucket not found', resource='', request_id='', host_id='', response='')
    except MinioException as exc:
        logger.error('Failed to connect to S3 service')
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f'Failed to connect to S3 service: {exc}')


async def check_main_service_health():
    async with AsyncClient() as client:
        service_key = config.BACKEND_SECRET_KEY
        url = MAIN_SERVICE_HEALTH_CHECK_URL
        headers = {'Token': service_key}

        try:
            response = await client.get(url=url, headers=headers)
            response.raise_for_status()
        except HTTPError:
            # TODO можно извлечь traceback
            logger.error('All connection to API Main attempts failed')
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='All connection to API Main attempts failed')


async def check_service_health():
    await check_minio()
    await check_main_service_health()
