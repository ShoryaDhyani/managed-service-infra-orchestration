import json
from logger import publish_log, publish_error
import aio_pika
from aio_pika import DeliveryMode, Message
from config import config


class RabbitMQ:

    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue = None

    async def connect(self):
        publish_log("Connecting to RabbitMQ...")
        try:
            self.connection = await aio_pika.connect_robust(
            config.rabbitmq_url
            )
        except Exception as e:
            publish_error(f"Error connecting to RabbitMQ: {e}")
            raise
        publish_log("Connected to RabbitMQ")
        self.channel = await self.connection.channel()

        await self.channel.set_qos(prefetch_count=1)

        self.queue = await self.channel.declare_queue(
            "build.queue",
            durable=True
        )

    async def publish(self, message: dict):
        publish_log("Publishing message to RabbitMQ...")
        await self.channel.default_exchange.publish(
            Message(
                body=json.dumps(message).encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
            ),
            routing_key="build.queue",
        )

    async def close(self):
        publish_log("Closing RabbitMQ connection...")
        await self.connection.close()


rabbitmq = RabbitMQ()