"""Teste le pipeline complet avec de faux scrapers, une base en mémoire et un faux serveur SMTP."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Notification, Offer, ScrapeRun, Source, Subscriber
from app.scrapers.base import BaseScraper, ScrapedOffer
from app.services import notifier, pipeline


class WorkingScraper(BaseScraper):
    name = "Site qui marche"

    def fetch_offers(self):
        return [
            ScrapedOffer(title="Stage Data Scientist", url="https://a.ma/1", company="Oracle", location="Fès",
                         description="Python, machine learning et analyse de données"),
            ScrapedOffer(title="Stagiaire Marketing digital", url="https://a.ma/2", company="Atlas", location="Rabat",
                         description="Communication, réseaux sociaux et contenu"),
        ]


class BrokenScraper(BaseScraper):
    name = "Site en panne"

    def fetch_offers(self):
        raise RuntimeError("le site ne répond pas")


class FakeSMTP:
    """Remplace smtplib.SMTP : note les destinataires au lieu d'envoyer un vrai e-mail."""
    sent_to: list[str] = []
    refused: set[str] = set()

    def __init__(self, *args):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def ehlo(self):
        pass

    def starttls(self):
        pass

    def login(self, *args):
        pass

    def send_message(self, message):
        if message["To"] in self.refused:
            raise RuntimeError("adresse refusée")
        self.sent_to.append(message["To"])


def subscriber(email: str, keywords: str, is_active: bool = True) -> Subscriber:
    return Subscriber(email=email, keywords=keywords, is_active=is_active, unsubscribe_token=f"jeton-{email}")


@pytest.fixture
def session_factory(monkeypatch):
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as db:
        db.add_all([
            Source(name="Site en panne", base_url="x"),
            Source(name="Site qui marche", base_url="y"),
            subscriber("data@exemple.ma", "data science, python, machine learning"),
            subscriber("marketing@exemple.ma", "marketing, communication, réseaux sociaux"),
            subscriber("droit@exemple.ma", "droit, juridique, contentieux"),
            subscriber("ancien@exemple.ma", "data science, python", is_active=False),
        ])
        db.commit()
    FakeSMTP.sent_to, FakeSMTP.refused = [], set()
    monkeypatch.setattr(notifier.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(pipeline, "SessionLocal", factory)
    monkeypatch.setattr(pipeline, "SCRAPERS", [BrokenScraper(), WorkingScraper()])
    return factory


def test_a_broken_site_does_not_stop_the_others(session_factory):
    assert pipeline.run_pipeline()["new_offers"] == {"Site en panne": 0, "Site qui marche": 2}
    with session_factory() as db:
        statuses = {run.source.name: run.status for run in db.query(ScrapeRun)}
        assert statuses == {"Site en panne": "error", "Site qui marche": "success"}
        assert db.query(Offer).count() == 2
        assert all(source.last_run_at for source in db.query(Source))


def test_each_active_subscriber_gets_only_matching_offers(session_factory):
    assert pipeline.run_pipeline()["emails_sent"] == 2
    # Ni l'abonné sans offre correspondante ni l'abonné désinscrit ne reçoivent d'e-mail.
    assert sorted(FakeSMTP.sent_to) == ["data@exemple.ma", "marketing@exemple.ma"]
    with session_factory() as db:
        sent = {(n.subscriber_id, n.offer_id) for n in db.query(Notification)}
        data = db.query(Subscriber).filter_by(email="data@exemple.ma").one()
        offer = db.query(Offer).filter_by(title="Stage Data Scientist").one()
        assert len(sent) == 2 and (data.id, offer.id) in sent


def test_second_run_sends_nothing(session_factory):
    pipeline.run_pipeline()
    summary = pipeline.run_pipeline()
    assert summary == {"new_offers": {"Site en panne": 0, "Site qui marche": 0}, "emails_sent": 0}
    assert len(FakeSMTP.sent_to) == 2


def test_a_failed_email_does_not_stop_the_others(session_factory):
    FakeSMTP.refused = {"data@exemple.ma"}
    assert pipeline.run_pipeline()["emails_sent"] == 1
    assert FakeSMTP.sent_to == ["marketing@exemple.ma"]
    with session_factory() as db:
        assert db.query(Notification).count() == 1  # rien n'est noté comme envoyé pour l'e-mail refusé


def test_an_offer_is_never_sent_twice_to_the_same_subscriber(session_factory):
    pipeline.run_pipeline()
    with session_factory() as db:
        data = db.query(Subscriber).filter_by(email="data@exemple.ma").one()
        offers = db.query(Offer).all()
        notifier.send_digest(db, data, [(offer, 0.5) for offer in offers])
        # Seule l'offre pas encore envoyée à cet abonné part dans ce second e-mail.
        assert db.query(Notification).filter_by(subscriber_id=data.id).count() == 2
    assert FakeSMTP.sent_to.count("data@exemple.ma") == 2