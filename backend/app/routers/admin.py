"""Routes d'administration."""
from fastapi import APIRouter

from app.services.pipeline import run_pipeline

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/scrape")
def scrape():
    """Lance le pipeline tout de suite, sans attendre le scheduler (utile pour la démo)."""
    return run_pipeline()