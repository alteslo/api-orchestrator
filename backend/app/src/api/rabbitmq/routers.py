import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.configs.settings import get_settings
from app.src.api.rabbitmq.client import RabbitMQClient
from app.src.api.rabbitmq.constants import RMQ_QUEUE_NAME
from app.src.api.rabbitmq.deps import get_rabbitmq_client, get_rabbitmq_http_client

rabbitmq_router = APIRouter()
config = get_settings()


@rabbitmq_router.get(path="/queue_info", tags=["rabbitmq"])
async def queue_info(queue_name: str, client: RabbitMQClient = Depends(get_rabbitmq_client)):
    """Возвращает список объектов относящихся к переданной сущности"""
    try:
        return await client.get_queue_info(RMQ_QUEUE_NAME)  # TODO Переделать, передавать queue_name
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@rabbitmq_router.get(path="/list_queues", tags=["rabbitmq"])
async def list_queues(client: httpx.AsyncClient = Depends(get_rabbitmq_http_client)):
    """Возвращает список объектов относящихся к переданной сущности"""
    vhost = ""
    try:
        response = await client.get(f"/queues/{vhost}")    # TODO Переделать, например сделать отдельный клиент RabbitMQManagementClient
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Vhost not found")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=e.response.text
        )


@rabbitmq_router.put(path="/set_rabbitmq_config", tags=["rabbitmq"])
async def set_rabbitmq_config(client: RabbitMQClient = Depends(get_rabbitmq_client)):
    try:
        return await client.setup_infrastructure()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
