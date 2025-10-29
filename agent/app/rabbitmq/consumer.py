import json
import aio_pika
from app.config import settings
from app.llm.chain import run_agent_async
from app.rabbitmq.producer import send_response_async
from app.utils.logger import logger

async def handle_message(message: aio_pika.IncomingMessage):
    async with message.process():
        try:
            data = json.loads(message.body.decode())
            question = data.get("question", "")
            history = data.get("history", [])
            meta = data.get("meta", {})

            logger.info(f"Received: {question}")
            answer = await run_agent_async(question, history, meta)

            response = {
                "session_id": meta.get("session_id"),
                "answer": answer
            }
            await send_response_async(response)
            logger.info(f"Answer sent for {meta.get('session_id')}")

        except Exception as e:
            logger.error(f"Error handling message: {e}")

async def start_consumer():
    global connection, channel

    # 异步建立连接
    connection = await aio_pika.connect_robust(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        login=settings.RABBITMQ_USER,
        password=settings.RABBITMQ_PASSWORD
    )
    channel = await connection.channel()
    queue = await channel.declare_queue(settings.REQUEST_QUEUE, durable=True)

    async def handle_message(message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                raw_body = message.body.decode('utf-8', errors='ignore')
                data = json.loads(raw_body)
                logger.info(f"Received message: {data}")

                question = data.get("question")
                history = data.get("history", [])
                meta = data.get("meta", {})
                correlation_id = data.get("correlationId")
                answer = await run_agent_async(question, history, meta)

                response = {
                    "correlationId": correlation_id,
                    "reply": answer
                }
                await send_response_async(response)
                logger.info(f"Response sent for {correlation_id}")

            except Exception as e:
                logger.error(f"Error handling message: {e}", exc_info=True)

    await queue.consume(handle_message)
    logger.info("RabbitMQ consumer started")