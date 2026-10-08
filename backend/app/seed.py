"""Insère les sites suivis dans la table sources. Lancer : python -m app.seed"""
from app.database import SessionLocal , Base , engine
from app.models import Source

SOURCES = [
    {"name": "Jobsquare", "base_url": "https://www.jobsquare.ma/jobs/"},
    {"name": "Stage", "base_url": "https://www.stage.ma/offres-stage"},
]

Base.metadata.create_all(bind=engine)

with SessionLocal() as db:
    for source in SOURCES:
        if not db.query(Source).filter_by(name=source["name"]).first():
            db.add(Source(**source))
    db.commit()
    print([s.name for s in db.query(Source).all()])