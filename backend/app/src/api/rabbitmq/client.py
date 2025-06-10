# from app.models import Saga
import json
from pathlib import Path
from typing import Any

import aio_pika
from aio_pika.abc import AbstractChannel, AbstractRobustConnection

from app.configs.settings import get_settings
from app.src.api.rabbitmq.base import BaseMessageBroker
from app.src.api.rabbitmq.constants import (
    DLX_EXCHANGE_NAME,
    DLX_QUEUE_NAME,
    RMQ_EXCHANGE_NAME,
    RMQ_PASS,
    RMQ_PORT,
    RMQ_QUEUE_NAME,
    RMQ_ROUTING_KEY,
    RMQ_USER
)
from app.src.core.logging import logger

from api.rabbitmq.schemas import RMQDestinationType

config = get_settings()


class RabbitMQClient(BaseMessageBroker):
    def __init__(self, config_file: str = "app/configs/load_definition.json"):
        self.connection: AbstractRobustConnection | None = None
        self.channel: AbstractChannel | None = None
        self.exchange: aio_pika.Exchange | None = None
        self.dlx_exchange: aio_pika.Exchange | None = None
        self.orchestrator_queue: aio_pika.Queue | None = None
        self.config_file = config_file
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

    async def setup_infrastructure(self):
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
        """Creates necessary exchanges, queues and bindings from config file"""
        await self._load_config()

        # If config is empty, use default settings
        if not self.infrastructure_config:
            logger.info("Using default RabbitMQ infrastructure setup")
            await self._setup_default_infrastructure()
            return

        created_queues = []
        created_exchanges = []

        # Create exchanges from config
        if 'exchanges' in self.infrastructure_config:
            for exchange_config in self.infrastructure_config['exchanges']:
                created_exchange = await self.channel.declare_exchange(
                    name=exchange_config['name'],
                    type=exchange_config['type'],
                    durable=exchange_config['durable'],
                    auto_delete=exchange_config['auto_delete'],
                    internal=exchange_config.get('internal', False),
                    arguments=exchange_config.get('arguments', {})
                )
                created_exchanges.append(created_exchange)

        # Create queues from config
        if 'queues' in self.infrastructure_config:
            for queue_config in self.infrastructure_config['queues']:
                created_queue = await self.channel.declare_queue(
                    name=queue_config['name'],
                    durable=queue_config['durable'],
                    auto_delete=queue_config['auto_delete'],
                    arguments=queue_config.get('arguments', {})
                )
                created_queues.append(created_queue)

        # Create bindings from config
        if 'bindings' in self.infrastructure_config:
            for binding_config in self.infrastructure_config['bindings']:

                for queue in created_queues:
                    if binding_config['destination_type'] == RMQDestinationType.QUEUE and binding_config['destination'] in created_queues:
                        await queue.bind(
                            exchange=binding_config['source'],
                            routing_key=binding_config['routing_key'],
                            arguments=binding_config.get('arguments', {})
                        )
                for exchange in created_exchanges:
                    if binding_config['destination_type'] == RMQDestinationType.EXCHANGE and binding_config['destination'] in created_exchanges:
                        await exchange.bind(
                            exchange=binding_config['source'],
                            routing_key=binding_config['routing_key'],
                            arguments=binding_config.get('arguments', {})
                        )

        logger.info("RabbitMQ infrastructure setup from config completed")

    async def _setup_default_infrastructure(self) -> None:
        """Fallback default infrastructure setup if config file is not provided"""
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

        logger.info("Default RabbitMQ infrastructure setup completed")

    async def consume_events(self, callback) -> None:
        """Запускает потребителя событий"""
        pass

    async def stop_consuming(self, topic: str):
        pass

    async def close(self) -> None:
        """Закрывает соединение с RabbitMQ"""
        if self.connection:
            await self.connection.close()

    async def get_queue_info(self, queue_name: str) -> dict:
        """Возвращает информацию об очереди"""
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

    async def list_queues(self, exchange_name: str):
        exchange = await self.channel.get_exchange(exchange_name)

        queue_names = []
        async for queue_name in exchange.list_queues():
            queue_names.append(queue_name)
        return queue_names


    # async def publish_saga_command(self, saga: Saga, step: int) -> None:
    #     """Публикует команду для выполнения шага саги"""
    #     step_data = saga.steps[step]
    #     routing_key = f"{step_data.service}.{step_data.command}"

    #     message = {
    #         "saga_id": saga.id,
    #         "step": step,
    #         "payload": saga.payload,
    #         "command": step_data.command
    #     }

    #     await self.exchange.publish(
    #         aio_pika.Message(
    #             body=json.dumps(message).encode(),
    #             delivery_mode=aio_pika.DeliveryMode.PERSISTENT
    #         ),
    #         routing_key=routing_key
    #     )

    # async def publish_compensation(self, saga: Saga, step: int) -> None:
    #     """Публикует команду компенсации"""
    #     step_data = saga.steps[step]
    #     routing_key = f"{step_data.service}.{step_data.compensation}"

    #     message = {
    #         "saga_id": saga.id,
    #         "step": step,
    #         "payload": saga.payload,
    #         "compensation": step_data.compensation
    #     }

    #     await self.exchange.publish(
    #         aio_pika.Message(
    #             body=json.dumps(message).encode(),
    #             delivery_mode=aio_pika.DeliveryMode.PERSISTENT
    #         ),
    #         routing_key=routing_key
    #     )
