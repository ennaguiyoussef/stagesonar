"""Teste le pipeline avec de faux scrapers et une base en mémoire : ni réseau ni PostgreSQL."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Offer, ScrapeRun, Source
from app.scrapers.base import BaseScraper, ScrapedOffer
from app.services import pipeline


class WorkingScraper(BaseScraper):
    name = "Site qui marche"

    def fetch_offers(self):
        return [ScrapedOffer(title="Stage data", url="https://a.ma/1", company="Oracle", location="Fès")]


class BrokenScraper(BaseScraper):
    name = "Site en panne"

    def fetch_offers(self):
        raise RuntimeError("le site ne répond pas")


@pytest.fixture
def session_factory(monkeypatch):
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as db:
        db.add_all([Source(name="Site en panne", base_url="x"), Source(name="Site qui marche", base_url="y")])
        db.commit()
    monkeypatch.setattr(pipeline, "SessionLocal", factory)
    monkeypatch.setattr(pipeline, "SCRAPERS", [BrokenScraper(), WorkingScraper()])
    return factory


def test_a_broken_site_does_not_stop_the_others(session_factory):
    assert pipeline.run_pipeline() == {"Site en panne": 0, "Site qui marche": 1}
    with session_factory() as db:
        statuses = {run.source.name: run.status for run in db.query(ScrapeRun)}
        assert statuses == {"Site en panne": "error", "Site qui marche": "success"}
        assert db.query(Offer).count() == 1
        assert all(source.last_run_at for source in db.query(Source))


def test_second_run_reports_zero_new_offers(session_factory):
    pipeline.run_pipeline()
    assert pipeline.run_pipeline()["Site qui marche"] == 0
    with session_factory() as db:
        assert db.query(ScrapeRun).count() == 4  # 2 sources x 2 exécutions
