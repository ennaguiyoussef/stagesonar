"""Scraper du site A (à renommer d'après le site choisi)."""
from app.scrapers.base import BaseScraper, ScrapedOffer


class SiteAScraper(BaseScraper):
    name = "Site A"
    base_url = ""

    def fetch_offers(self) -> list[ScrapedOffer]:
        # TODO (jour 2) : self.get(self.base_url), parser avec BeautifulSoup,
        # renvoyer une liste de ScrapedOffer.
        raise NotImplementedError
