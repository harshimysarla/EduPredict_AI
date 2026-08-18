import sys
import os
import traceback
from pathlib import Path

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


def _make_fallback_app():
    """Return a minimal FastAPI app that explains the startup error."""
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    fallback = FastAPI()

    @fallback.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
    def catch_all(path: str = ""):
        return JSONResponse(
            status_code=503,
            content={"detail": "EduPredict AI backend is starting up. Please try again in a moment."},
        )
    return fallback


try:
    from app.core.database import init_db
    from app.main import app

    # Initialize DB tables + seed on cold start
    try:
        init_db()
    except Exception:
        pass  # Don't let DB init failure crash the function

except Exception:
    traceback.print_exc()
    app = _make_fallback_app()

handler = app
__all__ = ["app", "handler"]
