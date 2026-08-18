import os
import tempfile

# ── resolve writable dirs ──────────────────────────────────────────
_IS_LINUX = (os.name != "nt")
_TMP = tempfile.gettempdir()

_DEFAULT_DB = (
    f"sqlite:///{_TMP}/edupredict.db" if _IS_LINUX else "sqlite:///./edupredict.db"
)
_DEFAULT_MODELS = os.path.join(_TMP, "models") if _IS_LINUX else "./models"
_ATLAS_URI = (
    "mongodb+srv://harshimysarla_db_user:vggZGd2D2d1Y7kbM"
    "@cluster0.mcqyqtp.mongodb.net/edupredict_ai"
    "?retryWrites=true&w=majority&appName=Cluster0"
)


def _int_env(name: str, default: int) -> int:
    """Read an env var as int; return default when missing or empty."""
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _str_env(name: str, default: str) -> str:
    """Read an env var as str; return default when missing or empty."""
    raw = os.environ.get(name, "").strip()
    return raw if raw else default


def _db_url() -> str:
    """
    Return a usable DATABASE_URL.
    If the configured URL points to localhost/127.0.0.1 or is empty,
    fall back to SQLite (safe for Vercel serverless).
    """
    raw = _str_env("DATABASE_URL", _DEFAULT_DB)
    if "localhost" in raw or "127.0.0.1" in raw:
        return _DEFAULT_DB
    return raw


class _Settings:
    """Lightweight settings object — no pydantic, no .env loading on Vercel."""

    DATABASE_URL: str = _db_url()
    SECRET_KEY: str = _str_env(
        "SECRET_KEY",
        "edupredict-ai-production-super-secret-key-2026-secure-32chars",
    )
    ALGORITHM: str = _str_env("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = _int_env("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
    FRONTEND_URL: str = _str_env("FRONTEND_URL", "*")
    MODEL_PATH: str = _str_env("MODEL_PATH", _DEFAULT_MODELS)
    RANDOM_SEED: int = _int_env("RANDOM_SEED", 42)
    MONGODB_URI: str = _str_env("MONGODB_URI", _ATLAS_URI)
    MONGODB_DB_NAME: str = _str_env("MONGODB_DB_NAME", "edupredict_ai")
    SAMVIDHA_API_BASE_URL: str = _str_env("SAMVIDHA_API_BASE_URL", "")
    SAMVIDHA_CLIENT_ID: str = _str_env("SAMVIDHA_CLIENT_ID", "")
    SAMVIDHA_CLIENT_SECRET: str = _str_env("SAMVIDHA_CLIENT_SECRET", "")


settings = _Settings()