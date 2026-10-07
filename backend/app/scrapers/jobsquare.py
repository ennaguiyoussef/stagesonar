"""Scraper de Jobsquare.ma.

Le robots.txt du site autorise /jobs/ et les fiches /job/..., mais interdit les
URL contenant searchId (pages 2, 3, ...) : on ne lit donc que la première page,
qui est triée de l'offre la plus récente à la plus ancienne.
"""
import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, ScrapedOffer

INTERNSHIP = re.compile(r"\bstag(e|iaire)s?\b", re.IGNORECASE)


def text(card, selector: str) -> str:
    """Texte d'un élément de la carte, espaces nettoyés ; chaîne vide s'il est absent."""
    element = card.select_one(selector)
    return " ".join(element.get_text().split()) if element else ""


class JobsquareScraper(BaseScraper):
    name = "Jobsquare"
    base_url = "https://www.jobsquare.ma/jobs/"

    def fetch_offers(self) -> list[ScrapedOffer]:
        return self.parse(self.get(self.base_url))

    def parse(self, html: str) -> list[ScrapedOffer]:
        """Transforme le HTML de la page de liste en offres de stage."""
        offers = []
        for card in BeautifulSoup(html, "html.parser").select("div.sj-job-card"):
            title = text(card, ".sj-card-title a")
            # La liste mélange emplois et stages : on ne garde que les stages.
            if text(card, ".sj-type") != "Stage" and not INTERNSHIP.search(title):
                continue
            date = text(card, ".sj-card-date")  # "07/10/2026", vide pour les offres épinglées
            offers.append(
                ScrapedOffer(
                    title=title,
                    url=card.select_one(".sj-card-title a")["href"],
                    company=text(card, ".sj-card-company a"),
                    location=text(card, ".sj-loc").removesuffix(", Maroc"),
                    description=text(card, ".sj-card-desc"),
                    published_at=(
                        datetime.strptime(date, "%d/%m/%Y").replace(tzinfo=timezone.utc) if date else None
                    ),
                )
            )
        return offers