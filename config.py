from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URL: str
    OPENAI_API_KEY: str
    DATABASE_NAME: str

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()
