from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
import tempfile

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


def _get_default_database_url() -> str:
    if os.name != "nt":
        return f"sqlite:///{os.path.join(tempfile.gettempdir(), 'edupredict.db')}"
    return "sqlite:///./edupredict.db"


def _get_default_model_path() -> str:
    if os.name != "nt":
        return os.path.join(tempfile.gettempdir(), "models")
    return "./models"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_find_env(),
        case_sensitive=True,
        extra="ignore",
    )

    DATABASE_URL: str = _get_default_database_url()
    SECRET_KEY: str = "edupredict-ai-production-super-secret-key-2026-secure-32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    FRONTEND_URL: str = "http://localhost:5173"
    MODEL_PATH: str = _get_default_model_path()
    RANDOM_SEED: int = 42
    MONGODB_URI: str = "mongodb+srv://harshimysarla_db_user:vggZGd2D2d1Y7kbM@cluster0.mcqyqtp.mongodb.net/edupredict_ai?retryWrites=true&w=majority&appName=Cluster0"
    MONGODB_DB_NAME: str = "edupredict_ai"
    # Future official IARE/Samvidha integration (leave empty; NOT used today)
    SAMVIDHA_API_BASE_URL: str = ""
    SAMVIDHA_CLIENT_ID: str = ""
    SAMVIDHA_CLIENT_SECRET: str = ""


settings = Settings()