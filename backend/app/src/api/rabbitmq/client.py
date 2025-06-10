import json
from pathlib import Path
from typing import Any

import aio_pika
from aio_pika.abc import AbstractChannel, AbstractRobustConnection

from app.configs.settings import get_settings
from app.src.api.rabbitmq.base import BaseAMQPBroker
from app.src.api.rabbitmq.constants import (
    DLX_EXCHANGE_NAME,
    DLX_QUEUE_NAME,
    RMQ_EXCHANGE_NAME,
    RMQ_PASS,
    RMQ_PORT,
    RMQ_QUEUE_NAME,
    RMQ_ROUTING_KEY,
    RMQ_USER,
    SYSTEM_EXCHANGE_NAME,
    SYSTEM_NOTIFICATION_QUEUE_NAME,
    SYSTEM_ROUTING_KEY
)
from app.src.core.logging import logger

from api.rabbitmq.schemas import RMQDestinationType

config = get_settings()

QueueInfo = dict[str, Any]  # TODO переделать в нормальный тип
ExchangeInfo = dict[str, Any]  # TODO переделать в нормальный тип


class RabbitMQClient(BaseAMQPBroker):
    def __init__(self):
        self.connection: AbstractRobustConnection | None = None
        self.channel: AbstractChannel | None = None
        self.exchange: aio_pika.Exchange | None = None
        self.dlx_exchange: aio_pika.Exchange | None = None
        self.orchestrator_queue: aio_pika.Queue | None = None
        self.config_file: Path = Path("app/configs/load_definition.json")
        self.infrastructure_config: dict[str, Any] = {}

    async def connect(self) -> None:
        """Устанавливает соединение с RabbitMQ и настраивает инфраструктуру"""
        self.connection = await aio_pika.connect_robust(
            host='rabbitmq-local',
            port=RMQ_PORT,
            login=RMQ_USER,
            password=RMQ_PASS,
        )
        self.channel = await self.connection.channel()

    async def setup_infrastructure(self, config_file: str | Path | None = None):
        """Основная точка входа для настройки инфраструктуры."""
        if config_file:
            self.config_file = Path(config_file)
        await self._setup_infrastructure()

    async def _load_config(self) -> None:
        """Load infrastructure configuration from JSON file"""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self.infrastructure_config = json.load(f)
            else:
                logger.warning(f"Config file {self.config_file} not found, using default settings")
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            raise

    async def _setup_infrastructure(self) -> None:
        """Основной метод настройки инфраструктуры."""
        if not self.channel:
            logger.error("Канал не инициализирован")
            raise RuntimeError("Сначала вызовите connect()")

        await self._load_config()

        if not self.infrastructure_config:
            logger.info("Используется дефолтная инфраструктура")
            await self._setup_default_infrastructure()
            return

        await self._setup_exchanges_from_config()
        await self._setup_queues_from_config()
        await self._setup_bindings_from_config()

        # Если есть очередь из конфига — отправить событие
        queues = self.infrastructure_config.get('queues', [])
        for queue in queues:
            await self.publish_configuration_ready(queue['name'], queue.get('default_routing_key', '#'))

        logger.info("Инфраструктура RabbitMQ успешно создана")

    async def _setup_exchanges_from_config(self) -> None:
        """Создаёт обменники из конфига."""
        exchanges = self.infrastructure_config.get('exchanges', [])
        for exchange_cfg in exchanges:
            await self.channel.declare_exchange(
                name=exchange_cfg['name'],
                type=exchange_cfg['type'],
                durable=exchange_cfg.get('durable', False),
                auto_delete=exchange_cfg.get('auto_delete', False),
                internal=exchange_cfg.get('internal', False),
                arguments=exchange_cfg.get('arguments', {})
            )

    async def _setup_queues_from_config(self) -> None:
        """Создаёт очереди из конфига."""
        queues = self.infrastructure_config.get('queues', [])
        for queue_cfg in queues:
            await self.channel.declare_queue(
                name=queue_cfg['name'],
                durable=queue_cfg.get('durable', False),
                auto_delete=queue_cfg.get('auto_delete', False),
                arguments=queue_cfg.get('arguments', {})
            )

    async def _setup_bindings_from_config(self) -> None:
        """Создаёт привязки из конфига."""
        bindings = self.infrastructure_config.get('bindings', [])
        for binding in bindings:
            if binding['destination_type'] == RMQDestinationType.QUEUE:
                queue = await self.channel.get_queue(binding['destination'])
                await queue.bind(
                    exchange=binding['source'],
                    routing_key=binding['routing_key'],
                    arguments=binding.get('arguments', {})
                )
            elif binding['destination_type'] == RMQDestinationType.EXCHANGE:
                exchange = await self.channel.get_exchange(binding['destination'])
                await exchange.bind(
                    exchange=binding['source'],
                    routing_key=binding['routing_key'],
                    arguments=binding.get('arguments', {})
                )

    async def _setup_default_infrastructure(self) -> None:
        """Создаёт дефолтную инфраструктуру, если конфиг не найден."""
        self.exchange = await self.channel.declare_exchange(
            name=RMQ_EXCHANGE_NAME,
            type='topic',
            durable=True
        )
        self.dlx_exchange = await self.channel.declare_exchange(
            name=DLX_EXCHANGE_NAME,
            type='topic',
            durable=True
        )

        # Create DLQ and bind to DLX
        dlx_queue = await self.channel.declare_queue(
            name=DLX_QUEUE_NAME,
            durable=True,
            arguments={'x-queue-type': 'classic'}
        )
        await dlx_queue.bind(exchange=DLX_EXCHANGE_NAME, routing_key='#')

        # Arguments for queues with DLX settings
        queue_args = {
            'x-dead-letter-exchange': DLX_EXCHANGE_NAME,
            'x-dead-letter-routing-key': DLX_QUEUE_NAME,
            'x-queue-type': 'classic'
        }

        # Create main queues with DLX settings
        main_queue = await self.channel.declare_queue(
            name=RMQ_QUEUE_NAME,
            durable=True,
            arguments=queue_args
        )

        # Bind queue to exchange
        await main_queue.bind(
            exchange=RMQ_EXCHANGE_NAME,
            routing_key=RMQ_ROUTING_KEY
        )

        # Setup system notification infrastructure
        system_exchange = await self.channel.declare_exchange(
            name=SYSTEM_EXCHANGE_NAME,
            type='topic',
            durable=True
        )

        system_queue = await self.channel.declare_queue(
            name=SYSTEM_NOTIFICATION_QUEUE_NAME,
            durable=True
        )

        await system_queue.bind(system_exchange, routing_key=SYSTEM_ROUTING_KEY)

        logger.info("Дефолтная инфраструктура настроена")

    async def publish_configuration_ready(self, queue_name: str, routing_key: str):
        """
        Публикует событие о готовности очереди в системный обменник.

        :param queue_name: Имя очереди, которая была создана
        :param routing_key: Роутинг ключ, по которому она доступна
        """
        if not self.channel:
            logger.error("Канал не инициализирован")
            raise RuntimeError("Сначала вызовите connect()")

        try:
            event = {
                "event_type": "configuration_ready",
                "queue_name": queue_name,
                "routing_key": routing_key
            }

            message = aio_pika.Message(
                body=json.dumps(event).encode(),
                content_type="application/json",
                delivery_mode=2  # persistent message
            )

            await self.channel.default_exchange.publish(
                message=message,
                routing_key=SYSTEM_ROUTING_KEY
            )

            logger.info(f"Событие configuration_ready опубликовано для {queue_name} с ключом {routing_key}")
        except Exception as e:
            logger.error(f"Ошибка при публикации события configuration_ready: {e}")
            raise

    async def consume_events(self, callback) -> None:
        """Запускает потребителя событий"""
        pass

    async def stop_consuming(self, topic: str):
        pass

    async def close(self) -> None:
        """Закрывает соединение с RabbitMQ"""
        if self.connection:
            await self.connection.close()
            logger.info("Соединение с RabbitMQ закрыто")

    async def get_queue_info(self, queue_name: str) -> QueueInfo:
        """Возвращает информацию о конкретной очереди."""
        try:
            queue = await self.channel.declare_queue(
                queue_name,
                passive=True  # Только проверка существования
            )
            return {
                "name": queue.name,
                "messages": queue.declaration_result.message_count,
                "consumers": queue.declaration_result.consumer_count
            }
        except Exception as e:
            return {"name": queue_name, "error": str(e)}
