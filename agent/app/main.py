import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.models.message import AgentRequest
from app.llm.chain import run_agent_async
from app.rabbitmq.consumer import start_consumer
from app.utils.logger import logger

app = FastAPI(title="Async LangChain Agent Service")

# ---------------- Lifespan 生命周期管理 ----------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 应用启动逻辑
    logger.info("Starting RabbitMQ consumer...")
    consumer_task = asyncio.create_task(start_consumer())

    try:
        yield  # 应用运行期间
    finally:
        # 应用关闭逻辑
        logger.info("Shutting down RabbitMQ consumer...")
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            logger.info("Consumer task cancelled successfully.")

# 将 Lifespan 注入 FastAPI
app.router.lifespan_context = lifespan

# ---------------- REST 接口 ----------------
@app.post("/chat")
async def chat(request: AgentRequest):
    """REST接口 手动请求LLM"""
    answer = await run_agent_async(request.question, request.history, request.meta)
    return {"answer": answer}

@app.get("/")
async def root():
    return {"status": "ok", "service": "Async Agent"}

import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10027)