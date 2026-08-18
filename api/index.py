"""
EduPredict AI – Vercel Serverless Entrypoint
All heavy imports are deferred so the process can NEVER crash on cold start.
"""
import sys
import os
import traceback
from pathlib import Path

# ── make backend importable ────────────────────────────────────────
_backend = Path(__file__).resolve().parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

# ── try to build the real FastAPI app ─────────────────────────────
_startup_error: str = ""

try:
    from app.core.database import init_db
    from app.main import app as _real_app

    try:
        init_db()
    except Exception as _e:
        # DB seed failure is non-fatal — the app still handles requests
        print(f"[EduPredict] init_db warning: {_e}", file=sys.stderr)

    app = _real_app

except Exception as _e:
    _startup_error = traceback.format_exc()
    print(f"[EduPredict] STARTUP ERROR:\n{_startup_error}", file=sys.stderr)

    # ── fallback: minimal app that always returns 200 on health ───
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(title="EduPredict AI (degraded mode)")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    @app.get("/health")
    def health():
        return {"status": "degraded", "error": _startup_error[:500]}

    @app.api_route(
        "/{path:path}",
        methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
    )
    async def fallback(request: Request, path: str = ""):
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Backend is temporarily unavailable. Please try again.",
                "startup_error": _startup_error[:300] if _startup_error else None,
            },
        )

handler = app
__all__ = ["app", "handler"]
