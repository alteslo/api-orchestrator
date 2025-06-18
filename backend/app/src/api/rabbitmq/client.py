import json
from pathlib import Path
from typing import Any, Optional

import aio_pika
from aio_pika import ExchangeType, Message
from aio_pika.abc import AbstractChannel, AbstractRobustConnection

from app.configs.settings import get_settings
from app.src.api.rabbitmq.base import AMQPChannelFactory, AMQPConnectionFactory, BaseAMQPBroker
from app.src.api.rabbitmq.constants import (
    DLX_EXCHANGE_NAME,
    DLX_QUEUE_NAME,
    RMQ_EXCHANGE_NAME,
    RMQ_PASS,
    RMQ_PORT,
    RMQ_QUEUE_NAME,
    RMQ_ROUTING_KEY,
    RMQ_USER,
    SYSTEM_EXCHANGE_NAME
)
from app.src.api.rabbitmq.schemas import (
    ConfigReadyEvent,
    InfrastructureConfig,
    RabbitMQEventType,
    RMQDestinationType,
    ServiceConfig
)
from app.src.core.logging import logger

config = get_settings()

QueueInfo = dict[str, Any]
ExchangeInfo = dict[str, Any]


# TODO Разделение ответственности: вынести публикацию событий в отдельный класс.
# TODO Импорты: получать константы из конфига.
# TODO Retry-логика для соединения
# TODO Health-check методы
# TODO Механизм подтверждения (ack/nack) для сообщений
# TODO Переделать обработку ошибок


class InfrastructureLoader:
    @staticmethod
    def load(path: Path) -> InfrastructureConfig:
        """Загружает JSON-конфигурацию из файла."""
        if not path.exists():
            raise FileNotFoundError(f"Config file {path} not found")
        with open(path, 'r') as f:
            data = json.load(f)
        return InfrastructureConfig(**data)


class RabbitMQClient(BaseAMQPBroker):
    def __init__(
        self,
        connection: AbstractRobustConnection | None = None,
        channel: AbstractChannel | None = None,
        connection_factory: Optional[AMQPConnectionFactory] = None,
        channel_factory: AMQPChannelFactory | None = None
    ):
        # Зависимости
        self.connection: AbstractRobustConnection | None = connection
        self.channel: AbstractChannel | None = channel
        self._connection_factory = connection_factory or self._default_connection_factory
        self._channel_factory = channel_factory or self._default_channel_factory

        # Конфигурация
        self.config_file: Path = Path("app/configs/load_definition.json")
        self.infrastructure_config: InfrastructureConfig | None = None

    # ==== Методы жизненного цикла ====
    async def connect(self) -> None:
        """Устанавливает соединение с RabbitMQ."""
        if not self.connection:
            self.connection = await self._connection_factory()
        if not self.channel:
            self.channel = await self._channel_factory(self.connection)
        logger.info("Соединение с RabbitMQ установлено")

    async def close(self) -> None:
        """Закрывает соединение с RabbitMQ"""
        if self.connection:
            await self.connection.close()
            logger.info("Соединение с RabbitMQ закрыто")

    # ==== Общее API / Бизнесс логика ====
    async def setup_infrastructure(self, config_file: str | Path | None = None):
        """Основная точка входа для настройки инфраструктуры."""
        if config_file:
            self.config_file = Path(config_file)
        await self._setup_infrastructure()

    async def publish_configuration_ready(self, services_config: list[ServiceConfig]):
        """
        Публикует событие о готовности очереди в системный обменник.
        :param queue_name: Имя очереди, которая была создана
        :param routing_key: Роутинг ключ, по которому она доступна
        """

        if not self.channel:
            logger.error("Канал не инициализирован")
            raise RuntimeError("Сначала вызовите connect()")

        system_exchange = await self.channel.declare_exchange(
            name=SYSTEM_EXCHANGE_NAME,
            type=ExchangeType.TOPIC,
            durable=True
        )

        for service in services_config:

            service_name = service.service_name
            service_routing_key = service.service_routing_key
            service_binding_conf = service.service_binding_conf

            system_queue = await self.channel.declare_queue(name=service_name, durable=True)
            await system_queue.bind(system_exchange, routing_key=service_routing_key)

            ready_event = ConfigReadyEvent(
                event_type=RabbitMQEventType.CONFIG_READY,
                payload=service_binding_conf
            )

            try:

                message = Message(
                    body=ready_event.model_dump_json().encode(),
                    content_type="application/json",
                    delivery_mode=2  # persistent message
                )

                await system_exchange.publish(
                    message=message,
                    routing_key=service_routing_key
                )

                logger.info(f"Событие configuration_ready опубликовано для {service_name} с ключом {service_routing_key}")
            except Exception as e:
                logger.error(f"Ошибка при публикации события configuration_ready: {e}")
                raise

    # ==== Приватные методы / помощники ====
    async def _load_config(self) -> None:
        """Загружает JSON-конфигурацию из файла."""
        try:
            config_path = Path(self.config_file)
            self.infrastructure_config = InfrastructureLoader.load(config_path)
        except Exception as e:
            logger.error(f"Ошибка при загрузке конфига: {e}")
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
        logger.info("Инфраструктура RabbitMQ успешно создана")

        if self.infrastructure_config.services_config:
            await self.publish_configuration_ready(self.infrastructure_config.services_config)

    async def _setup_exchanges_from_config(self) -> None:
        """Создаёт обменники из конфига."""
        exchanges = self.infrastructure_config.exchanges
        for exchange_cfg in exchanges:
            await self.channel.declare_exchange(
                name=exchange_cfg.name,
                type=exchange_cfg.type,
                durable=exchange_cfg.durable,
                auto_delete=exchange_cfg.auto_delete,
                internal=exchange_cfg.internal,
                arguments=exchange_cfg.arguments
            )

    async def _setup_queues_from_config(self) -> None:
        """Создаёт очереди из конфига."""
        queues = self.infrastructure_config.queues
        for queue_cfg in queues:
            await self.channel.declare_queue(
                name=queue_cfg.name,
                durable=queue_cfg.durable,
                auto_delete=queue_cfg.auto_delete,
                arguments=queue_cfg.arguments
            )

    async def _setup_bindings_from_config(self) -> None:
        """Создаёт привязки из конфига."""
        bindings = self.infrastructure_config.bindings
        for binding in bindings:
            if binding.destination_type == RMQDestinationType.QUEUE:
                queue = await self.channel.get_queue(binding.destination)
                await queue.bind(
                    exchange=binding.source,
                    routing_key=binding.routing_key,
                    arguments=binding.arguments
                )
            elif binding['destination_type'] == RMQDestinationType.EXCHANGE:
                exchange = await self.channel.get_exchange(binding['destination'])
                await exchange.bind(
                    exchange=binding.source,
                    routing_key=binding.routing_key,
                    arguments=binding.arguments
                )

    async def _setup_default_infrastructure(self) -> None:
        """Создаёт дефолтную инфраструктуру, если конфиг не найден."""
        exchange = await self.channel.declare_exchange(
            name=RMQ_EXCHANGE_NAME,
            type=ExchangeType.TOPIC,
            durable=True
        )
        dlx_exchange = await self.channel.declare_exchange(
            name=DLX_EXCHANGE_NAME,
            type=ExchangeType.TOPIC,
            durable=True
        )

        dlx_queue = await self.channel.declare_queue(name=DLX_QUEUE_NAME, durable=True, arguments={'x-queue-type': 'classic'})
        await dlx_queue.bind(exchange=dlx_exchange, routing_key='#')

        queue_args = {
            'x-dead-letter-exchange': DLX_EXCHANGE_NAME,
            'x-dead-letter-routing-key': DLX_QUEUE_NAME,
            'x-queue-type': 'classic'
        }

        main_queue = await self.channel.declare_queue(name=RMQ_QUEUE_NAME, durable=True, arguments=queue_args)
        await main_queue.bind(exchange=exchange, routing_key=RMQ_ROUTING_KEY)

        logger.info("Дефолтная инфраструктура настроена")

    # ==== Фабрики по умолчанию (могут быть переопределены с помощью DI) ====
    async def _default_connection_factory(self) -> AbstractRobustConnection:
        return await aio_pika.connect_robust(
            host='rabbitmq-local',
            port=RMQ_PORT,
            login=RMQ_USER,
            password=RMQ_PASS,
        )

    async def _default_channel_factory(self, connection: AbstractRobustConnection) -> AbstractChannel:
        return await connection.channel()

    # ==== Методы Consumer ====
    async def consume_events(self, callback) -> None:
        """Запускает потребителя событий"""
        pass

    async def stop_consuming(self, topic: str):
        pass

    # ==== Прикладные методы ====
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
