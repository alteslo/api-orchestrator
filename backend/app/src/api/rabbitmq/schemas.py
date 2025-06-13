from pydantic import BaseModel
from enum import Enum
from app.configs.settings import get_settings

config = get_settings()


class RMQDestinationType(Enum):
    QUEUE = 'queue'
    EXCHANGE = 'exchange'


class QueueConfig(BaseModel):
    name: str
    vhost: str = "/"
    durable: bool = True
    auto_delete: bool = False
    arguments: dict = {}


# === Exchange Config ===
class ExchangeConfig(BaseModel):
    name: str
    vhost: str = "/"
    type: str  # direct, topic, fanout и т.д.
    durable: bool = False
    auto_delete: bool = False
    internal: bool = False
    arguments: dict = {}


# === Binding Config ===
class BindingConfig(BaseModel):
    source: str
    vhost: str = "/"
    destination: str
    destination_type: RMQDestinationType
    routing_key: str
    arguments: dict = {}


# === Service Config (необязательно, но удобно) ===
class RetryPolicyConfig(BaseModel):
    max_attempts: int = 3
    delay_ms: int = 1000


class ServiceConfig(BaseModel):
    queue: str
    routing_key: str
    dlq_enabled: bool = False
    prefetch_count: int = 100
    retry_policy: RetryPolicyConfig | None = None


class SystemConfig(BaseModel):
    service_name: str
    service_routing_key: str
    service_config: ServiceConfig


class InfrastructureConfig(BaseModel):
    queues: list[QueueConfig | None] = []
    exchanges: list[ExchangeConfig | None] = []
    bindings: list[BindingConfig | None] = []
    services_config: list[SystemConfig] | None = None
