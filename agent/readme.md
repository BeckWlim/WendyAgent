# General Agent Runtime

Python agent is now a general runtime behind the existing Java Gateway/Auth stack.
It keeps the RabbitMQ contract used by `common-service`, while adding runtime
boundaries for memory, persistence, RAG, controlled tools, and task workers.

## Capabilities

- FastAPI control plane and compatibility `/chat` endpoint.
- RabbitMQ request/response bridge for Java WebSocket traffic.
- Markdown Memory Vault under `data/memory_vault` by default.
- SQLite structured persistence under `data/agent_runtime.sqlite3` by default.
- PostgreSQL-backed RAG document store.
- Tool Registry with allowlisted built-in tools.
- Task Manager with async workers for orchestration.

## Runtime Modules

- `app/runtime`: runtime orchestration and request/result schemas.
- `app/memory`: Markdown Memory Vault.
- `app/persistence`: structured SQLite store.
- `app/rag`: PostgreSQL vector document store and deterministic hash embeddings.
- `app/tools`: allowlisted Tool Registry.
- `app/tasks`: in-process task queue and workers.
- `app/rabbitmq`: Java integration bridge.

## Environment

```Shell
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
REQUEST_QUEUE=agent.request.queue
RESPONSE_QUEUE=agent.response.queue
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

DEEPSEEK_API_KEY=...
MODEL_NAME=deepseek-chat

MEMORY_VAULT_PATH=data/memory_vault
AGENT_DB_PATH=data/agent_runtime.sqlite3
RAG_POSTGRES_DSN=postgresql://postgres:postgres@localhost:5432/llm
RAG_POSTGRES_TABLE=agent_rag_documents
RAG_POSTGRES_CONNECT_TIMEOUT=5
RAG_TOP_K=4
TOOL_ALLOWLIST=memory.search,memory.write,rag.search,rag.upsert
WORKER_CONCURRENCY=2
```

## Startup

```Shell
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 10027
```

## Control Plane

```Shell
GET  /
GET  /tools
POST /chat
POST /tools/call
POST /tasks
```

Built-in tasks:

- `tool.call`: execute an allowlisted tool in a worker.
- `memory.index_vault`: index Markdown Vault notes into the vector store.

## Build

```Shell
pyinstaller --onefile --name agent --additional-hooks-dir=hooks app/main.py
```
