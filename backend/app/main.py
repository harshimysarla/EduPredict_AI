import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import (
    auth, students, predictions, interventions, analytics, datasets,
    models, notifications, reports, meta, admin, portal,
)
from app.core.config import settings
from app.core.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("edupredict")


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# 2. Also mount under /api/index.py in case Vercel rewrites preserve the full entrypoint file path
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