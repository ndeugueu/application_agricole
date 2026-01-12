"""
Event-driven architecture utilities for RabbitMQ
Implements Outbox pattern for reliable event publishing
"""
import json
import os
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Callable
import pika
import structlog
from pydantic import BaseModel

logger = structlog.get_logger()


class EventEnvelope(BaseModel):
    """Standard event envelope for all domain events"""
    event_id: str
    event_type: str
    occurred_at: str
    producer: str
    correlation_id: str
    idempotency_key: Optional[str] = None
    payload: Dict[str, Any]


class EventPublisher:
    """RabbitMQ event publisher with connection management"""

    def __init__(self, rabbitmq_url: str, service_name: str):
        self.rabbitmq_url = rabbitmq_url
        self.service_name = service_name
        self.connection = None
        self.channel = None

    def connect(self):
        """Establish connection to RabbitMQ"""
        retries = int(os.getenv("RABBITMQ_CONNECT_RETRIES", "10"))
        delay_s = float(os.getenv("RABBITMQ_CONNECT_DELAY_SECONDS", "2"))
        last_error = None

        for attempt in range(1, retries + 1):
            try:
                self.connection = pika.BlockingConnection(
                    pika.URLParameters(self.rabbitmq_url)
                )
                self.channel = self.connection.channel()
                # Declare exchange for domain events
                self.channel.exchange_declare(
                    exchange='domain_events',
                    exchange_type='topic',
                    durable=True
                )
                logger.info("Connected to RabbitMQ", service=self.service_name)
                return
            except Exception as e:
                last_error = e
                logger.error(
                    "Failed to connect to RabbitMQ",
                    error=str(e),
                    service=self.service_name,
                    attempt=attempt,
                    retries=retries,
                )
                time.sleep(delay_s)

        raise last_error

    def publish_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ):
        """Publish an event to RabbitMQ"""
        if not self.channel or self.channel.is_closed:
            self.connect()

        event = EventEnvelope(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            occurred_at=datetime.utcnow().isoformat(),
            producer=self.service_name,
            correlation_id=correlation_id or str(uuid.uuid4()),
            idempotency_key=idempotency_key,
            payload=payload
        )

        try:
            self.channel.basic_publish(
                exchange='domain_events',
                routing_key=event_type,
                body=json.dumps(event.model_dump()),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent message
                    content_type='application/json',
                    correlation_id=event.correlation_id
                )
            )
            logger.info(
                "Event published",
                event_type=event_type,
                event_id=event.event_id,
                correlation_id=event.correlation_id
            )
        except Exception as e:
            logger.error("Failed to publish event", error=str(e), event_type=event_type)
            raise

    def close(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("RabbitMQ connection closed", service=self.service_name)


class EventConsumer:
    """RabbitMQ event consumer with handler registration"""

    def __init__(self, rabbitmq_url: str, service_name: str, queue_name: str):
        self.rabbitmq_url = rabbitmq_url
        self.service_name = service_name
        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self.handlers: Dict[str, Callable] = {}
        self.processed_events = set()  # Simple idempotency check

    def connect(self):
        """Establish connection to RabbitMQ"""
        retries = int(os.getenv("RABBITMQ_CONNECT_RETRIES", "10"))
        delay_s = float(os.getenv("RABBITMQ_CONNECT_DELAY_SECONDS", "2"))
        last_error = None

        for attempt in range(1, retries + 1):
            try:
                self.connection = pika.BlockingConnection(
                    pika.URLParameters(self.rabbitmq_url)
                )
                self.channel = self.connection.channel()
                self.channel.exchange_declare(
                    exchange='domain_events',
                    exchange_type='topic',
                    durable=True
                )
                self.channel.queue_declare(queue=self.queue_name, durable=True)
                logger.info("Event consumer connected", service=self.service_name, queue=self.queue_name)
                return
            except Exception as e:
                last_error = e
                logger.error(
                    "Failed to connect event consumer",
                    error=str(e),
                    service=self.service_name,
                    queue=self.queue_name,
                    attempt=attempt,
                    retries=retries,
                )
                time.sleep(delay_s)

        raise last_error

    def register_handler(self, event_type: str, handler: Callable):
        """Register a handler for a specific event type"""
        self.handlers[event_type] = handler
        if self.channel:
            self.channel.queue_bind(
                exchange='domain_events',
                queue=self.queue_name,
                routing_key=event_type
            )
        logger.info("Event handler registered", event_type=event_type, service=self.service_name)

    def _on_message(self, ch, method, properties, body):
        """Callback for processing messages"""
        try:
            event_data = json.loads(body)
            event = EventEnvelope(**event_data)

            # Idempotency check
            if event.event_id in self.processed_events:
                logger.warning("Duplicate event ignored", event_id=event.event_id)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # Find and execute handler
            handler = self.handlers.get(event.event_type)
            if handler:
                logger.info("Processing event", event_type=event.event_type, event_id=event.event_id)
                handler(event)
                self.processed_events.add(event.event_id)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                logger.warning("No handler for event type", event_type=event.event_type)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        except Exception as e:
            logger.error("Error processing event", error=str(e))
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start_consuming(self):
        """Start consuming messages"""
        if not self.channel:
            self.connect()

        self.channel.basic_qos(prefetch_count=10)
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self._on_message
        )

        logger.info("Started consuming events", service=self.service_name)
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.stop_consuming()

    def stop_consuming(self):
        """Stop consuming messages"""
        if self.channel:
            self.channel.stop_consuming()
        self.close()

    def close(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("Event consumer connection closed", service=self.service_name)
