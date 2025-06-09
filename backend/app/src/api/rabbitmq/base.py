from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class BaseMessageBroker(ABC):
    @abstractmethod
    async def connect(self):
        ...

    # @abstractmethod
    # async def publish_saga_command(self, saga: Saga, step: int) -> None:
    #     ...

    # @abstractmethod
    # async def publish_compensation(self, saga: Saga, step: int):
    #     ...

    @abstractmethod
    async def consume_events(self, callback) -> None:
        ...

    @abstractmethod
    async def stop_consuming(self, topic: str):
        ...

    @abstractmethod
    async def get_queue_info(self, queue_name: str):
        ...

    @abstractmethod
    async def close(self):
        ...
