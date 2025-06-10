from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.configs.settings import get_settings
from app.src.api.rabbitmq.client import RabbitMQClient
from app.src.api.rabbitmq.routers import rabbitmq_router
from app.src.core.logging import logger

config = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):

    rabbitmq_client = RabbitMQClient()
    try:
        await rabbitmq_client.connect()
        await rabbitmq_client.setup_infrastructure()
    except Exception as e:
        logger.error(f"Не удалось подключиться к RabbitMQ: {e}")
        raise  # Останавливаем запуск при неудачном подключении

    # Сохраняем клиент в app.state
    app.state.rabbitmq_client = rabbitmq_client
    logger.info("Клиент RabbitMQ успешно инициализирован")

    yield

    rabbitmq_client.close()


if config.ENVIRONMENT_NAME in ("prod",):
    docs_url = None
    redoc_url = None
else:
    docs_url = "/docs"
    redoc_url = "/redoc"

app = FastAPI(
    lifespan=lifespan,
    docs_url=docs_url,
    redoc_url=redoc_url,
    title=config.FILES_PROJECT_NAME,
    summary="Прототип сервиса оркестратора системы ISET, обеспечивает обмен сообщениями между сервисами.",
    version=config.FILES_VERSION if config.FILES_VERSION else "",
    swagger_ui_parameters={
        "syntaxHighlight": False,
        "deepLinking": False,
        "layout": "BaseLayout",
        "showExtensions": False,
        "showCommonExtensions": False,
    },
    description="",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rabbitmq_router, prefix=config.FILES_API_PREFIX)
