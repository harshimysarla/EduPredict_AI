"""
EduPredict AI - Vercel Serverless Entrypoint.

Vercel builds this file as a Python function. Its static analyzer recognizes
the app only when the entrypoint CONSTRUCTS the framework app directly
(e.g. `app = FastAPI(...)`), not when it re-exports an import. So this file
creates the FastAPI app and mounts the real backend application on it.
"""
import sys
from pathlib import Path

# ── make backend importable ────────────────────────────────────────
_backend = Path(__file__).resolve().parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from fastapi import FastAPI  # noqa: E402
from app.main import app as _backend_app  # noqa: E402

# `app` is the entrypoint the Vercel Python runtime loads. It must be
# constructed directly in this file for the build-time analyzer to detect it.
app = FastAPI(title="EduPredict AI")
app.mount("/", _backend_app)

from app.core.database import init_db  # noqa: E402

# ── seed tables / ensure DB exists (non-fatal on failure) ──────────
try:
    init_db()
except Exception as _e:
    print(f"[EduPredict] init_db warning: {_e}", file=sys.stderr)

__all__ = ["app"]