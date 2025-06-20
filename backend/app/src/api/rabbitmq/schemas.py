from typing import Any

from app.src.api.rabbitmq.constants import RMQDestinationType
from pydantic import BaseModel

from app.configs.settings import get_settings

config = get_settings()


# === Схемы настройки конфигурации rabbitmq ===
class QueueConfig(BaseModel):
    name: str
    vhost: str = "/"
    durable: bool = True
    auto_delete: bool = False
    arguments: dict = {}


class ExchangeConfig(BaseModel):
    name: str
    vhost: str = "/"
    type: str  # direct, topic, fanout и т.д.
    durable: bool = False
    auto_delete: bool = False
    internal: bool = False
    arguments: dict = {}


class BindingConfig(BaseModel):
    source: str
    vhost: str = "/"
    destination: str
    destination_type: RMQDestinationType
    routing_key: str
    arguments: dict = {}


# === Схемы настройки конфигурации потребителей (динамическая подписка) ===
class RetryPolicyConfig(BaseModel):
    max_attempts: int = 3
    delay_ms: int = 1000


class ServiceBindingConfig(BaseModel):
    exchange: str
    queue: str
    routing_key: str
    vhost: str = "/"
    durable: bool = False
    auto_delete: bool = False
    arguments: dict = {}
    prefetch_count: int = 100
    retry_policy: RetryPolicyConfig | None = None


class ServiceConfig(BaseModel):
    service_name: str
    service_routing_key: str
    service_binding_conf: list[ServiceBindingConfig]


class InfrastructureConfig(BaseModel):
    queues: list[QueueConfig | None] = []
    exchanges: list[ExchangeConfig | None] = []
    bindings: list[BindingConfig | None] = []
    services_config: list[ServiceConfig] | None = None


# === События RMQ ===
class Event(BaseModel):
    """Базовая схема события"""
    event_type: str
    payload: Any


class ConfigReadyEvent(Event):
    ...
