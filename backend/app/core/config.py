from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

_BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_REPO = os.path.dirname(_BASE)


def _find_env() -> str:
    candidates = [
        os.path.join(_REPO, ".env"),
        os.path.join(_BASE, ".env"),
        os.path.join(os.getcwd(), ".env"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return os.path.join(_BASE, ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_find_env(), case_sensitive=True)

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    FRONTEND_URL: str = "http://localhost:5173"
    MODEL_PATH: str = "./models"
    RANDOM_SEED: int = 42
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "edupredict_ai"
    # Future official IARE/Samvidha integration (leave empty; NOT used today)
    SAMVIDHA_API_BASE_URL: str = ""
    SAMVIDHA_CLIENT_ID: str = ""
    SAMVIDHA_CLIENT_SECRET: str = ""


settings = Settings()