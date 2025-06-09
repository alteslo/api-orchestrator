from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.src.api.auth.routers import router as auth_router
from app.src.api.health_check.routers import router as api_router
from app.src.api.objects.routers import router as objects_router
from app.configs.settings import get_settings
from app.src.core.exception_handlers.app_exceptions import register_custom_exc_handlers
from app.src.core.logging import logger

config = get_settings()


# === Lifespan для старта и остановки consumer ===
@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Started ORCHESTRATOR")

    # Запускаем consumer при старте
    # consumer = RabbitMQConsumer()
    # consumer_task = asyncio.create_task(consumer.consume())
    # logger.info("RabbitMQConsumer - Запущен")
    yield

    # await AsyncRedis.remove_cache_init_lock()
    # # Останавливаем consumer при завершении
    # await consumer.stop()
    # consumer_task.cancel()
    # try:
    #     await consumer_task
    # except asyncio.CancelledError:
    #     pass
    # logger.info("RabbitMQConsumer - Остановлен")
    logger.info("Stoped ORCHESTRATOR")


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
    terms_of_service="",
    contact={
        "name": "",
        "url": "",
        "email": "",
    },
    license_info={
        "name": "",
        "identifier": "",
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

if config.DEBUG:
    app.include_router(auth_router, prefix=config.FILES_API_PREFIX)

app.include_router(api_router)
app.include_router(objects_router, prefix=config.FILES_API_PREFIX)

register_custom_exc_handlers(app)
