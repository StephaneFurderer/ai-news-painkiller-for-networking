from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    openai_api_key: str
    telegram_bot_token: str
    authorized_user_id: int
    readwise_token: str
    max_message_length: int = 4000
    openai_model: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()