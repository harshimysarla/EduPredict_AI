"""
EduPredict AI - Vercel FastAPI entrypoint.

Vercel auto-detects the FastAPI framework preset (fastapi is declared in the
root requirements.txt / pyproject.toml). The preset requires a root-level
entrypoint exposing an `app` instance; this file imports the real application
from backend/app/main.py. The preset then routes every request to the app,
which serves both the /api endpoints and the built frontend (frontend/dist).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app.main import app  # noqa: E402

__all__ = ["app"]