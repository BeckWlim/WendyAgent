# 🧠 LangChain Agent Service

A lightweight **asynchronous agent service** built with **FastAPI**, **LangChain**, and **RabbitMQ**.
It listens to message queues, processes requests using LLMs, and returns responses asynchronously.

---

## 🚀 Features

- ⚡ **FastAPI + aio-pika** for async event-driven architecture
- 🤖 **LangChain** integration with OpenAI or other LLM providers
- 📬 **RabbitMQ consumer/producer** for message-based communication
- 🧩 Modular and production-ready code structure
- 🌐 REST endpoint for manual testing (`/chat`)

## Startup

```Shell
pip install -r requeirements.txt
uvicorn app.main:app
```
