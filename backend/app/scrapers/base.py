"""Contrat commun à tous les scrapers.

Chaque site a son module (site_a.py, site_b.py) avec une classe qui hérite de
BaseScraper et implémente fetch_offers(). Le reste de l'application ne connaît
que ScrapedOffer : il ne dépend jamais du HTML d'un site en particulier.
"""
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

import httpx

from app.config import settings


@dataclass
class ScrapedOffer:
    title: str
    url: str
    company: str = ""
    location: str = ""
    description: str = ""
    published_at: datetime | None = None


class BaseScraper(ABC):
    name: str = ""      # nom affiché, par exemple "Site A"
    base_url: str = ""  # page de liste des offres

    def get(self, url: str) -> str:
        """Télécharge une page en s'identifiant et en respectant un délai entre requêtes."""
        time.sleep(settings.request_delay_seconds)
        response = httpx.get(
            url,
            headers={"User-Agent": settings.user_agent},
            timeout=20,
            follow_redirects=True,
        )
        response.raise_for_status()
        return response.text

    @abstractmethod
    def fetch_offers(self) -> list[ScrapedOffer]:
        """Renvoie les offres visibles sur le site, dans le format commun."""