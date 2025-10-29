from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int = 5672

    REQUEST_QUEUE: str
    RESPONSE_QUEUE: str
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str

    DEEPSEEK_API_KEY: str
    MODEL_NAME: str = 'deeepseek-chat'

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()