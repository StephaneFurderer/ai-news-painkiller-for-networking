from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    readwise_token: str
    openai_model: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()