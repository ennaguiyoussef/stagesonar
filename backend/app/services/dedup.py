"""Détection des nouveautés : reconnaître une offre déjà vue grâce à son empreinte."""
import hashlib
import re
import unicodedata
from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Offer, Source
from app.scrapers.base import ScrapedOffer


def normalize(text: str) -> str:
    """Minuscules, sans accents, sans ponctuation, espaces réduits."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def compute_fingerprint(title: str, company: str, location: str) -> str:
    """SHA-256 de titre + entreprise + ville après normalisation."""
    key = "|".join(normalize(part) for part in (title, company, location))
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def save_new_offers(db: Session, source: Source, scraped_offers: list[ScrapedOffer]) -> list[Offer]:
    """Insère uniquement les offres jamais vues et les renvoie."""
    # 1. Une empreinte par offre. Le dictionnaire élimine les doublons du lot lui-même.
    candidates = {}
    for scraped in scraped_offers:
        fingerprint = compute_fingerprint(scraped.title, scraped.company, scraped.location)
        candidates.setdefault(fingerprint, Offer(source_id=source.id, fingerprint=fingerprint, **asdict(scraped)))

    # 2. Parmi ces empreintes, lesquelles sont déjà en base ?
    known = set(db.scalars(select(Offer.fingerprint).where(Offer.fingerprint.in_(candidates))))

    # 3. On n'insère que les autres.
    new_offers = [offer for fingerprint, offer in candidates.items() if fingerprint not in known]
    db.add_all(new_offers)
    db.commit()
    return new_offers