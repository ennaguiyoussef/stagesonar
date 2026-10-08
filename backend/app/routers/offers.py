"""Routes de consultation : offres, sources, statistiques."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Offer, Source
from app.schemas import OfferOut, SourceOut

router = APIRouter(prefix="/api", tags=["offres"])


@router.get("/offers")
def get_offers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = None,
    city: str | None = None,
    source: int | None = None,
    db: Session = Depends(get_db),
):
    """Retourne les offres paginées, avec filtres optionnels."""

    query = db.query(Offer)

    # Recherche dans le titre ou le nom de l'entreprise
    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                Offer.title.ilike(search),
                Offer.company.ilike(search),
            )
        )

    # Filtre par ville
    if city:
        query = query.filter(
            Offer.location.ilike(f"%{city}%")
        )

    # Filtre par source
    if source is not None:
        query = query.filter(
            Offer.source_id == source
        )

    # Plus récentes en premier
    query = query.order_by(
        Offer.first_seen_at.desc()
    )

    # Nombre total avant pagination
    total = query.count()

    # Pagination
    offset = (page - 1) * page_size

    offers = (
        query
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return {
        "items": [
            OfferOut.model_validate(offer)
            for offer in offers
        ],
        "total": total,
    }


@router.get("/sources")
def get_sources(
    db: Session = Depends(get_db),
):
    """Retourne les sites suivis et leur dernière exécution."""

    sources = (
        db.query(Source)
        .order_by(Source.name.asc())
        .all()
    )

    return [
        SourceOut.model_validate(source)
        for source in sources
    ]


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
):
    """
    Retourne :
    - le nombre d'offres par source ;
    - le nombre de nouvelles offres par jour
      sur les 7 derniers jours.
    """

    # ---------------------------------------------------------
    # 1. Nombre d'offres par source
    # ---------------------------------------------------------

    source_counts = (
        db.query(
            Source.id,
            Source.name,
            func.count(Offer.id).label("count"),
        )
        .outerjoin(
            Offer,
            Offer.source_id == Source.id,
        )
        .group_by(
            Source.id,
            Source.name,
        )
        .order_by(Source.name.asc())
        .all()
    )

    offers_by_source = [
        {
            "source_id": source_id,
            "source": source_name,
            "count": count,
        }
        for source_id, source_name, count in source_counts
    ]

    # ---------------------------------------------------------
    # 2. Nouvelles offres par jour
    # ---------------------------------------------------------

    now = datetime.now(timezone.utc)
    start_date = (
        now - timedelta(days=6)
    ).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    # PostgreSQL : date_trunc permet de regrouper par jour.
    daily_counts = (
        db.query(
            func.date(
                Offer.first_seen_at
            ).label("date"),
            func.count(Offer.id).label("count"),
        )
        .filter(
            Offer.first_seen_at >= start_date
        )
        .group_by(
            func.date(Offer.first_seen_at)
        )
        .order_by(
            func.date(Offer.first_seen_at)
        )
        .all()
    )

    counts_by_date = {
        str(date): count
        for date, count in daily_counts
    }

    new_offers_by_day = []

    for i in range(7):
        date = (
            start_date.date()
            + timedelta(days=i)
        )

        date_string = date.isoformat()

        new_offers_by_day.append(
            {
                "date": date_string,
                "count": counts_by_date.get(
                    date_string,
                    0,
                ),
            }
        )

    return {
        "offers_by_source": offers_by_source,
        "new_offers_by_day": new_offers_by_day,
    }