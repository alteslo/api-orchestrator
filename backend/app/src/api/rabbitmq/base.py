from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class BaseAMQPBroker(ABC):
    @abstractmethod
    async def connect(self):
        ...

    @abstractmethod
    async def setup_infrastructure(self):
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

    @abstractmethod
    async def close(self):
        ...
