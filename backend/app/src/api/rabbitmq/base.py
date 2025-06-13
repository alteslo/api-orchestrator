from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol

from aio_pika.abc import AbstractChannel, AbstractRobustConnection


@dataclass
class BaseAMQPBroker(ABC):
    @abstractmethod
    async def connect(self):
        ...

    @abstractmethod
    async def close(self):
        ...

    @abstractmethod
    async def setup_infrastructure(self):
        ...

    @abstractmethod
    async def publish_configuration_ready(self):
        ...

    @abstractmethod
    async def consume_events(self, callback) -> None:
        ...

    @abstractmethod
    async def stop_consuming(self, topic: str):
        ...

    @abstractmethod
    async def get_queue_info(self, queue_name: str):
        ...


class AMQPConnectionFactory(Protocol):
    async def __call__(self) -> AbstractRobustConnection:
        ...


class AMQPChannelFactory(Protocol):
    async def __call__(self, connection: AbstractRobustConnection) -> AbstractChannel:
        ...
