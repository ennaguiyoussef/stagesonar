"""Routes d'abonnement et de désinscription."""

import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Subscriber
from app.schemas import SubscriberCreate

router = APIRouter(prefix="/api/subscribers", tags=["abonnés"])


@router.post("")
def subscribe(
    subscriber_data: SubscriberCreate,
    db: Session = Depends(get_db),
):
    """Crée ou réactive un abonnement."""

    subscriber = (
        db.query(Subscriber)
        .filter(Subscriber.email == subscriber_data.email)
        .first()
    )

    if subscriber is not None:
        # L'email existe déjà : mise à jour et réactivation.
        subscriber.keywords = subscriber_data.keywords
        subscriber.location = subscriber_data.location
        subscriber.is_active = True

    else:
        # Nouvel abonnement.
        subscriber = Subscriber(
            email=subscriber_data.email,
            keywords=subscriber_data.keywords,
            location=subscriber_data.location,
            is_active=True,
            unsubscribe_token=secrets.token_urlsafe(32),
        )
        db.add(subscriber)

    db.commit()
    db.refresh(subscriber)

    # Ne jamais renvoyer l'email ou la liste des abonnés.
    return {
        "message": "Abonnement enregistré.",
        "unsubscribe_token": subscriber.unsubscribe_token,
    }


@router.delete("/{token}")
def unsubscribe(
    token: str,
    db: Session = Depends(get_db),
):
    """Désactive un abonnement à partir de son jeton."""

    subscriber = (
        db.query(Subscriber)
        .filter(Subscriber.unsubscribe_token == token)
        .first()
    )

    if subscriber is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jeton de désinscription inconnu.",
        )

    subscriber.is_active = False

    db.commit()

    return {
        "message": "Désinscription effectuée.",
    }