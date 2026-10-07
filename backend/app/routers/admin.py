"""Routes d'administration."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/admin", tags=["admin"])

# TODO (jour 3) : POST /api/admin/scrape   lancer le pipeline à la main (utile pour la démo)
