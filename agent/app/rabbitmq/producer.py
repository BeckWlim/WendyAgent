import json
import aio_pika
from app.config import settings
from app.utils.logger import logger

async def send_response_async(data: dict):
    try:
        connection = await aio_pika.connect_robust(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            login=settings.RABBITMQ_USER,
            password=settings.RABBITMQ_PASSWORD
        )
        channel = await connection.channel()
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(data).encode()),
            routing_key=settings.RESPONSE_QUEUE
        )
        await connection.close()
        logger.info(f"Response sent to {settings.RESPONSE_QUEUE}")
    except Exception as e:
        logger.error(f"Failed to send response: {e}")