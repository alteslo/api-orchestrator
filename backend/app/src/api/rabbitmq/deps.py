from functools import lru_cache
from typing import AsyncGenerator

import httpx
from fastapi import Request

from app.src.api.rabbitmq.constants import RMQ_PASS, RMQ_USER


@lru_cache
def get_rabbitmq_settings():
    return {
        "base_url": "http://rabbitmq-local:15672/api",
        "auth": (RMQ_USER, RMQ_PASS)
    }


async def get_rabbitmq_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    settings = get_rabbitmq_settings()
    async with httpx.AsyncClient(base_url=settings["base_url"]) as client:
        client.auth = settings["auth"]
        yield client


async def get_rabbitmq_client(request: Request):
    return request.app.state.rabbitmq_client
