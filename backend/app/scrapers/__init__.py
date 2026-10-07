"""Liste des scrapers lancés par le pipeline.

Le `name` de chaque scraper doit être identique au `name` de sa ligne dans la table sources.
"""
from app.scrapers.jobsquare import JobsquareScraper

SCRAPERS = [
    JobsquareScraper(),
    # Fouad : ajouter ici StageScraper() quand il est prêt.
]