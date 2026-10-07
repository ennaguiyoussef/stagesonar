"""Insère les sites suivis dans la table sources. Lancer : python -m app.seed"""
from app.database import SessionLocal
from app.models import Source

SOURCES = [
    {"name": "Jobsquare", "base_url": "https://www.jobsquare.ma/jobs/"},
    {"name": "Dreamjob", "base_url": "https://www.dreamjob.ma/stage/"},
]

with SessionLocal() as db:
    for source in SOURCES:
        if not db.query(Source).filter_by(name=source["name"]).first():
            db.add(Source(**source))
    db.commit()
    print([s.name for s in db.query(Source).all()])