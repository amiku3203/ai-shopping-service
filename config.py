from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URL: str
    OPENAI_API_KEY: str
    DATABASE_NAME: str
    FT_API_URL: str = "https://api-final-touch-mern.onrender.com"

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()
