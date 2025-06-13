RMQ_USER = "guest"
RMQ_PASS = "guest"
RMQ_PORT = 5672
RMQ_QUEUE_NAME = "main.events"
RMQ_EXCHANGE_NAME = "minio_events"
RMQ_ROUTING_KEY = "minio.bucket.events"

DLX_EXCHANGE_NAME = "minio_events_dlx"
DLX_QUEUE_NAME = "minio_events_dlq"
DLX_ROUTING_KEY = "minio_events_dlq"

SYSTEM_EXCHANGE_NAME = "system.exchange"
SYSTEM_NOTIFICATION_QUEUE_NAME = "system.notifications.main-local.queue"
SYSTEM_ROUTING_KEY = "system.event.configuration_ready"
