# from app.models import Saga
import aio_pika
from aio_pika.abc import AbstractChannel, AbstractRobustConnection

from app.configs.settings import get_settings
from app.src.api.rabbitmq.base import BaseMessageBroker
from app.src.api.rabbitmq.constants import DLX_EXCHANGE_NAME, DLX_QUEUE_NAME, RMQ_EXCHANGE_NAME, RMQ_PASS, RMQ_PORT, RMQ_QUEUE_NAME, RMQ_ROUTING_KEY, RMQ_USER
from app.src.core.logging import logger

config = get_settings()


class RabbitMQClient(BaseMessageBroker):
    def __init__(self):
        self.connection: AbstractRobustConnection | None = None
        self.channel: AbstractChannel | None = None
        self.exchange: aio_pika.Exchange | None = None
        self.dlx_exchange: aio_pika.Exchange | None = None
        self.orchestrator_queue: aio_pika.Queue | None = None

    async def connect(self) -> None:
        """Устанавливает соединение с RabbitMQ и настраивает инфраструктуру"""
        self.connection = await aio_pika.connect_robust(
            host='rabbitmq-local',
            port=RMQ_PORT,
            login=RMQ_USER,
            password=RMQ_PASS,
        )
        self.channel = await self.connection.channel()
        await self._setup_infrastructure()

    async def _setup_infrastructure(self) -> None:
        """Создает необходимые exchange, очереди и биндинги"""

        self.exchange = self.channel.exchange_declare(exchange=RMQ_EXCHANGE_NAME, exchange_type='topic', durable=True)  # Создаем exchange если не существует
        self.dlx_exchange = self.channel.exchange_declare(exchange=DLX_EXCHANGE_NAME, exchange_type='topic', durable=True)  # Создаем DLX exchange

        # Создаем DLQ и привязываем к DLX
        self.channel.queue_declare(queue=DLX_QUEUE_NAME, durable=True, arguments={'x-queue-type': 'classic'})
        self.channel.queue_bind(
            exchange=DLX_EXCHANGE_NAME,
            queue=DLX_QUEUE_NAME,
            routing_key='#'  # Принимаем все сообщения в DLQ
        )

        # Аргументы для очередей с настройкой DLX
        queue_args = {
            'x-dead-letter-exchange': DLX_EXCHANGE_NAME,
            'x-dead-letter-routing-key': DLX_QUEUE_NAME,
            'x-queue-type': 'classic'
        }

        # Создаем основные очереди с настройками DLX, если не существует
        self.channel.queue_declare(queue=RMQ_QUEUE_NAME, durable=True, arguments=queue_args)

        # Привязываем очередь к exchange
        self.channel.queue_bind(
            exchange=RMQ_EXCHANGE_NAME,
            queue=RMQ_QUEUE_NAME,
            routing_key=RMQ_ROUTING_KEY
        )

        logger.info("RabbitMQ infrastructure setup completed")

    async def consume_events(self, callback) -> None:
        """Запускает потребителя событий"""
        pass

    async def stop_consuming(self, topic: str):
        pass

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

    async def close(self) -> None:
        """Закрывает соединение с RabbitMQ"""
        if self.connection:
            await self.connection.close()

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
