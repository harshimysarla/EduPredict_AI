"""
EduPredict AI – Vercel Serverless Entrypoint.

Vercel builds this file as a Python function and requires a top-level ASGI
app. The `app` binding below is imported at DIRECT module level (Vercel's
scanner does not look inside try/except blocks), so it is always detected.
"""
import sys
from pathlib import Path

# ── make backend importable ────────────────────────────────────────
_backend = Path(__file__).resolve().parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from app.core.database import init_db  # noqa: E402
from app.main import app  # noqa: E402

# ── seed tables / ensure DB exists (non-fatal on failure) ──────────
try:
    init_db()
except Exception as _e:
    print(f"[EduPredict] init_db warning: {_e}", file=sys.stderr)

__all__ = ["app"]