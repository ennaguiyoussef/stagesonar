import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import Offer, Source
from app.scrapers.base import ScrapedOffer
from app.services.dedup import compute_fingerprint, save_new_offers


def test_same_offer_on_two_sites_gives_same_fingerprint():
    a = compute_fingerprint("Stage Data Scientist", "Société Générale", "Casablanca")
    b = compute_fingerprint("  stage data scientist ", "SOCIETE GENERALE", "casablanca.")
    assert a == b


def test_different_offers_give_different_fingerprints():
    a = compute_fingerprint("Stage Data Scientist", "Oracle", "Casablanca")
    b = compute_fingerprint("Stage Data Engineer", "Oracle", "Casablanca")
    assert a != b


@pytest.fixture
def db():
    """Base SQLite en mémoire, neuve pour chaque test : rien n'est écrit dans PostgreSQL."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(Source(name="Site test", base_url="https://exemple.ma"))
        session.commit()
        yield session


def offer(title: str) -> ScrapedOffer:
    return ScrapedOffer(title=title, url=f"https://exemple.ma/{title}", company="Oracle", location="Casablanca")


def test_second_run_finds_nothing_new(db):
    source = db.query(Source).one()
    batch = [offer("Stage data"), offer("Stage web"), offer("Stage RH")]
    assert len(save_new_offers(db, source, batch)) == 3
    assert len(save_new_offers(db, source, batch)) == 0
    assert db.query(Offer).count() == 3


def test_only_the_new_offer_is_returned(db):
    source = db.query(Source).one()
    save_new_offers(db, source, [offer("Stage data"), offer("Stage web"), offer("Stage RH")])
    new = save_new_offers(db, source, [offer("Stage data"), offer("Stage web"), offer("Stage RH"), offer("Stage IA")])
    assert [o.title for o in new] == ["Stage IA"]


def test_duplicate_inside_the_same_batch_is_stored_once(db):
    source = db.query(Source).one()
    new = save_new_offers(db, source, [offer("Stage data"), offer("STAGE  DATA")])
    assert len(new) == 1