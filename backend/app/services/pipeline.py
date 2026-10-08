"""Orchestration complète : collecte, détection des nouveautés, matching, envoi des e-mails."""
import logging

from app.database import SessionLocal
from app.models import ScrapeRun, Source, Subscriber, now_utc
from app.scrapers import SCRAPERS
from app.services.dedup import save_new_offers
from app.services.matcher import match_offers
from app.services.notifier import send_digest

logger = logging.getLogger("stagesonar")


def run_pipeline() -> dict:
    """Lance une collecte complète. Renvoie les nouvelles offres par source et le nombre d'e-mails envoyés."""
    new_per_source = {}
    new_offers = []
    emails_sent = 0

    with SessionLocal() as db:
        # 1 et 2. Collecte, puis détection des nouveautés, site par site.
        for scraper in SCRAPERS:
            source = db.query(Source).filter_by(name=scraper.name, is_active=True).first()
            if source is None:
                logger.warning("Scraper ignoré : aucune source active nommée %r dans la table sources", scraper.name)
                continue
            run = ScrapeRun(source_id=source.id)  # statut "running" par défaut
            db.add(run)
            db.commit()
            try:
                found = save_new_offers(db, source, scraper.fetch_offers())
                new_offers += found
                run.status, run.new_offers_count = "success", len(found)
            except Exception:
                # Un site en panne ne doit pas empêcher les autres d'être collectés.
                db.rollback()
                logger.exception("Échec du scraper %s", scraper.name)
                run.status = "error"
            source.last_run_at = now_utc()
            db.commit()
            new_per_source[scraper.name] = run.new_offers_count

        # 3. Matching : seules les nouvelles offres sont comparées aux abonnés actifs.
        subscribers = {s.id: s for s in db.query(Subscriber).filter_by(is_active=True)}
        matches = match_offers(new_offers, list(subscribers.values()))

        # 4. Notification : un e-mail par abonné concerné.
        for subscriber_id, scored_offers in matches.items():
            try:
                send_digest(db, subscribers[subscriber_id], scored_offers)
                emails_sent += 1
            except Exception:
                # Un envoi raté ne doit pas priver les autres abonnés de leur e-mail.
                db.rollback()
                logger.exception("Échec de l'envoi à l'abonné %s", subscriber_id)

    return {"new_offers": new_per_source, "emails_sent": emails_sent}