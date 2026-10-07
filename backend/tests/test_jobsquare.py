"""Teste le scraper Jobsquare sur une page enregistrée, sans appel réseau."""
from pathlib import Path

from app.scrapers.jobsquare import JobsquareScraper

HTML = (Path(__file__).parent / "fixtures" / "jobsquare_page1.html").read_text(encoding="utf-8")


def test_keeps_only_internships():
    offers = JobsquareScraper().parse(HTML)
    # La page enregistrée contient 23 offres, dont 5 stages.
    assert len(offers) == 5
    assert all("stag" in offer.title.lower() for offer in offers)


def test_every_offer_has_the_required_fields():
    for offer in JobsquareScraper().parse(HTML):
        assert offer.title and offer.company and offer.location
        assert offer.url.startswith("https://www.jobsquare.ma/job/")


def test_fields_of_a_known_offer():
    offer = next(o for o in JobsquareScraper().parse(HTML) if "/job/18850/" in o.url)
    assert offer.title == "Stagiaire en Ressources Humaines (H/F) | Marrakech"
    assert offer.location == "Marrakech, Marrakech-Safi"
    assert offer.published_at.date().isoformat() == "2026-10-07"


def test_pinned_offer_without_date():
    offer = next(o for o in JobsquareScraper().parse(HTML) if "/job/13488/" in o.url)
    assert offer.company == "CAD DIGITAL AGENCY"
    assert offer.published_at is None
