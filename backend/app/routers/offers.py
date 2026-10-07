"""Routes de consultation : offres, sources, statistiques."""
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["offres"])

# TODO (jour 3) : GET /api/offers   liste paginée, filtres q, city, source
# TODO (jour 3) : GET /api/sources  sites suivis et dernière exécution
# TODO (jour 3) : GET /api/stats    offres par source, nouvelles offres par jour
