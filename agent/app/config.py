from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672

    REQUEST_QUEUE: str = "agent.request.queue"
    RESPONSE_QUEUE: str = "agent.response.queue"
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"

    DEEPSEEK_API_KEY: str = ""
    MODEL_NAME: str = 'deepseek-chat'

    MEMORY_VAULT_PATH: str = "data/memory_vault"
    AGENT_DB_PATH: str = "data/agent_runtime.sqlite3"
    RAG_POSTGRES_DSN: str = "postgresql://postgres:postgres@localhost:5432/llm"
    RAG_POSTGRES_TABLE: str = "agent_rag_documents"
    RAG_POSTGRES_CONNECT_TIMEOUT: int = 5
    RAG_TOP_K: int = 4
    TOOL_ALLOWLIST: str = "memory.search,memory.write,rag.search,rag.upsert"
    WORKER_CONCURRENCY: int = 2

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
