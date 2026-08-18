from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
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


# Defaults for integer fields — used when env var is set to empty string
_INT_DEFAULTS = {
    "ACCESS_TOKEN_EXPIRE_MINUTES": 60,
    "RANDOM_SEED": 42,
}

# Defaults for string fields — used when env var is set to empty string
_STR_DEFAULTS = {
    "DATABASE_URL": _get_default_database_url(),
    "SECRET_KEY": "edupredict-ai-production-super-secret-key-2026-secure-32chars",
    "ALGORITHM": "HS256",
    "FRONTEND_URL": "http://localhost:5173",
    "MODEL_PATH": _get_default_model_path(),
    "MONGODB_URI": "mongodb+srv://harshimysarla_db_user:vggZGd2D2d1Y7kbM@cluster0.mcqyqtp.mongodb.net/edupredict_ai?retryWrites=true&w=majority&appName=Cluster0",
    "MONGODB_DB_NAME": "edupredict_ai",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_find_env(),
        case_sensitive=True,
        extra="ignore",
    )

    DATABASE_URL: str = _STR_DEFAULTS["DATABASE_URL"]
    SECRET_KEY: str = _STR_DEFAULTS["SECRET_KEY"]
    ALGORITHM: str = _STR_DEFAULTS["ALGORITHM"]
    ACCESS_TOKEN_EXPIRE_MINUTES: int = _INT_DEFAULTS["ACCESS_TOKEN_EXPIRE_MINUTES"]
    FRONTEND_URL: str = _STR_DEFAULTS["FRONTEND_URL"]
    MODEL_PATH: str = _STR_DEFAULTS["MODEL_PATH"]
    RANDOM_SEED: int = _INT_DEFAULTS["RANDOM_SEED"]
    MONGODB_URI: str = _STR_DEFAULTS["MONGODB_URI"]
    MONGODB_DB_NAME: str = _STR_DEFAULTS["MONGODB_DB_NAME"]
    SAMVIDHA_API_BASE_URL: str = ""
    SAMVIDHA_CLIENT_ID: str = ""
    SAMVIDHA_CLIENT_SECRET: str = ""

    @field_validator("ACCESS_TOKEN_EXPIRE_MINUTES", "RANDOM_SEED", mode="before")
    @classmethod
    def empty_str_to_default_int(cls, v, info):
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return _INT_DEFAULTS.get(info.field_name, 0)
        return v

    @field_validator(
        "DATABASE_URL", "SECRET_KEY", "ALGORITHM", "FRONTEND_URL",
        "MODEL_PATH", "MONGODB_URI", "MONGODB_DB_NAME",
        mode="before",
    )
    @classmethod
    def empty_str_to_default_str(cls, v, info):
        if isinstance(v, str) and v.strip() == "" and info.field_name in _STR_DEFAULTS:
            return _STR_DEFAULTS[info.field_name]
        return v


settings = Settings()