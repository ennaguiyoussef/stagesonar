"""Empreinte d'une offre : sert à reconnaître une offre déjà vue, même sur un autre site."""
import hashlib
import re
import unicodedata


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


# TODO (jour 2) : save_new_offers(db, source, scraped_offers) -> list[Offer]
# Insère uniquement les offres dont l'empreinte n'existe pas encore et les renvoie.
