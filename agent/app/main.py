import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.llm.chain import run_agent_async
from app.models.message import AgentRequest, TaskSubmitRequest, ToolCallRequest
from app.rabbitmq.consumer import start_consumer
from app.runtime.agent_runtime import get_runtime
from app.utils.logger import logger

app = FastAPI(title="General Agent Runtime")


@asynccontextmanager
async def lifespan(app: FastAPI):
    runtime = get_runtime()
    runtime.task_manager.start()
    logger.info("Starting RabbitMQ consumer...")
    consumer_task = asyncio.create_task(start_consumer())

    try:
        yield
    finally:
        logger.info("Shutting down RabbitMQ consumer...")
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            logger.info("Consumer task cancelled successfully.")
        await runtime.task_manager.stop()


app.router.lifespan_context = lifespan


@app.post("/chat")
async def chat(request: AgentRequest):
    answer = await run_agent_async(request.question, request.history, request.meta)
    return {"answer": answer}


@app.get("/tools")
async def list_tools():
    return {"tools": get_runtime().tools.list_tools()}


@app.post("/tools/call")
async def call_tool(request: ToolCallRequest):
    result = await get_runtime().call_tool(
        request.name,
        request.args,
        conversation_id=request.conversation_id,
        username=request.username,
    )
    return {"result": result}


@app.post("/tasks")
async def submit_task(request: TaskSubmitRequest):
    task = await get_runtime().task_manager.submit(request.kind, request.payload)
    return task.model_dump()


@app.get("/")
async def root():
    runtime = get_runtime()
    return {
        "status": "ok",
        "service": "General Agent Runtime",
        "tools": runtime.tools.list_tools(),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10027)
