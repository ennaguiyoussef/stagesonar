"""Routes d'abonnement et de désinscription."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/subscribers", tags=["abonnés"])

# TODO (jour 4) : POST   /api/subscribers           s'abonner (email, mots-clés, ville)
# TODO (jour 4) : DELETE /api/subscribers/{token}   se désabonner
