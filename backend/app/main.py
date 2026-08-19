import logging
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Scope, Receive, Send

from app.api import (
    auth, students, predictions, interventions, analytics, datasets,
    models, notifications, reports, meta, admin, portal,
)
from app.core.config import settings
from app.core.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("edupredict")


class VercelPathMiddleware:
    """
    ASGI middleware to resolve Vercel serverless rewritten paths.

    Vercel rewrites /api/(.*) -> /api/index.py. The Python function normally
    receives the ORIGINAL browser path in scope['path'] (so /api/auth/login
    matches the /api-prefixed router). Some setups only forward the destination
    (/api/index.py) and place the real URL in an x-*-path/uri header instead.
    This middleware restores the real path — tolerating full URLs, query
    strings and fragments — so the FastAPI router always finds the endpoint.
    """
    # Header candidates that may carry the original request path.
    _PATH_HEADERS = (
        b"x-matched-path",
        b"x-vercel-forwarded-uri",
        b"x-forwarded-uri",
        b"x-real-url",
    )
    # Vercel destination the /api rewrite resolves to (not a real endpoint).
    _DEST = "/api/index.py"

    def __init__(self, app: ASGIApp):
        self.app = app

    @staticmethod
    def _clean_path(raw: str) -> str:
        raw = (raw or "").strip()
        if not raw:
            return ""
        if raw.startswith(("http://", "https://")):
            raw = urlparse(raw).path
        if "?" in raw:
            raw = raw.split("?", 1)[0]
        if "#" in raw:
            raw = raw.split("#", 1)[0]
        if not raw.startswith("/"):
            raw = "/" + raw
        return raw

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []) or [])
            path = scope.get("path", "")

            restored = ""
            for key in self._PATH_HEADERS:
                value = headers.get(key)
                if value:
                    candidate = self._clean_path(value.decode("latin1"))
                    if candidate and candidate != self._DEST:
                        restored = candidate
                        break

            if restored:
                path = restored
            elif path.startswith(self._DEST):
                # Vercel may pass the destination with the real subpath appended.
                subpath = path[len(self._DEST):]
                path = ("/api" + subpath) if subpath else "/"

            if path and path != scope.get("path"):
                scope["path"] = path

        await self.app(scope, receive, send)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting EduPredict AI backend")
    try:
        init_db()
    except Exception as exc:
        logger.warning("Database init warning during startup: %s", exc)
    yield
    logger.info("Shutting down EduPredict AI backend")


app = FastAPI(
    title="EduPredict AI",
    description="AI-Powered Student Performance Predictor & Early Intervention Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Apply Vercel Path Middleware first so all routes receive the proper path
app.add_middleware(VercelPathMiddleware)

# CORS: allow the configured production origin plus local dev origins.
# Falls back to "*" (current permissive behaviour) when FRONTEND_URL is unset.
_frontend_origin = (settings.FRONTEND_URL or "").strip().rstrip("/")
_cors_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
if _frontend_origin and _frontend_origin != "*":
    _cors_origins.insert(0, _frontend_origin)
else:
    _cors_origins.insert(0, "*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# All standard routers
ROUTERS = [
    auth.router, meta.router, students.router, predictions.router,
    interventions.router, analytics.router, datasets.router, models.router,
    notifications.router, reports.router, admin.router, portal.router,
]

# 1. Mount under /api prefix for /api/... calls (standard Vite proxy / Vercel rewrite)
api_router = APIRouter(prefix="/api")
for r in ROUTERS:
    api_router.include_router(r)
app.include_router(api_router)

# 2. Also mount under /api/index.py as a fallback
api_index_router = APIRouter(prefix="/api/index.py")
for r in ROUTERS:
    api_index_router.include_router(r)
app.include_router(api_index_router)

# 3. Also mount at root for direct /auth, /students, etc.
for r in ROUTERS:
    app.include_router(r)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


@app.get("/")
@app.get("/api")
@app.get("/api/index.py")
def root():
    return {"app": "EduPredict AI", "status": "running", "docs": "/docs"}


@app.get("/health")
@app.get("/api/health")
@app.get("/api/index.py/health")
def health():
    from app.core.mongodb import check_mongo_status
    return {
        "status": "healthy",
        "mongodb": check_mongo_status(),
    }