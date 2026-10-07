"""Point d'entrée de l'API StageSonar."""
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  (enregistre les tables auprès de SQLAlchemy)
from app.config import settings
from app.database import Base, engine
from app.routers import admin, offers, subscribers
from app.services.pipeline import run_pipeline

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    scheduler.add_job(run_pipeline, "interval", hours=settings.scrape_interval_hours)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="StageSonar API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(offers.router)
app.include_router(subscribers.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok", "app": "StageSonar"}