from pydantic import BaseModel
from enum import Enum
from app.configs.settings import get_settings

config = get_settings()


class ObjectBase(BaseModel):
    bucket_name: str
    system_entity: str
    row_entity_id: str
    type_attachment: str


class RMQDestinationType(Enum):
    QUEUE = 'queue'
    EXCHANGE = 'exchange'
