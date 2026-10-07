"""Orchestration : collecte puis détection des nouveautés.

Le matching et l'envoi des e-mails seront ajoutés ici au jour 5.
"""
import logging

from app.database import SessionLocal
from app.models import ScrapeRun, Source, now_utc
from app.scrapers import SCRAPERS
from app.services.dedup import save_new_offers

logger = logging.getLogger("stagesonar")


def run_pipeline() -> dict[str, int]:
    """Lance chaque scraper actif. Renvoie le nombre de nouvelles offres par source."""
    summary = {}
    with SessionLocal() as db:
        for scraper in SCRAPERS:
            source = db.query(Source).filter_by(name=scraper.name, is_active=True).first()
            if source is None:
                continue
            run = ScrapeRun(source_id=source.id)  # statut "running" par défaut
            db.add(run)
            db.commit()
            try:
                new_offers = save_new_offers(db, source, scraper.fetch_offers())
                run.status, run.new_offers_count = "success", len(new_offers)
            except Exception:
                # Un site en panne ne doit pas empêcher les autres d'être collectés.
                db.rollback()
                logger.exception("Échec du scraper %s", scraper.name)
                run.status = "error"
            source.last_run_at = now_utc()
            db.commit()
            summary[scraper.name] = run.new_offers_count
    return summary
