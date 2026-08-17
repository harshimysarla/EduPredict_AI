import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import (
    auth, students, predictions, interventions, analytics, datasets,
    models, notifications, reports, meta, admin,
)
from app.core.config import settings
from app.core.database import Base, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("edupredict")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting EduPredict AI backend")
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
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(meta.router)
app.include_router(students.router)
app.include_router(predictions.router)
app.include_router(interventions.router)
app.include_router(analytics.router)
app.include_router(datasets.router)
app.include_router(models.router)
app.include_router(notifications.router)
app.include_router(reports.router)
app.include_router(admin.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


@app.get("/")
def root():
    return {"app": "EduPredict AI", "status": "running", "docs": "/docs"}