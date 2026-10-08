from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Offer, Source


def create_test_database():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


def test_get_offers():
    engine = create_test_database()

    with Session(engine) as db:
        source = Source(
            name="Site test",
            base_url="https://exemple.ma",
            is_active=True,
        )
        db.add(source)
        db.commit()
        db.refresh(source)

        db.add_all(
            [
                Offer(
                    source_id=source.id,
                    title="Stage Data Scientist",
                    company="Oracle",
                    location="Casablanca",
                    url="https://exemple.ma/data",
                    fingerprint="fingerprint-data",
                    published_at=datetime(2026, 10, 8, tzinfo=timezone.utc),
                    first_seen_at=datetime(
                        2026, 10, 8, 10, 0, tzinfo=timezone.utc
                    ),
                ),
                Offer(
                    source_id=source.id,
                    title="Stage Data Analyst",
                    company="IBM",
                    location="Rabat",
                    url="https://exemple.ma/analyst",
                    fingerprint="fingerprint-analyst",
                    published_at=datetime(2026, 10, 7, tzinfo=timezone.utc),
                    first_seen_at=datetime(
                        2026, 10, 7, 10, 0, tzinfo=timezone.utc
                    ),
                ),
            ]
        )
        db.commit()

    def override_get_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            response = client.get("/api/offers")

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["title"] == "Stage Data Scientist"
        assert data["items"][1]["title"] == "Stage Data Analyst"

    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_get_sources():
    engine = create_test_database()

    with Session(engine) as db:
        db.add_all(
            [
                Source(
                    name="Stage.ma",
                    base_url="https://www.stage.ma",
                    is_active=True,
                    last_run_at=datetime(
                        2026, 10, 8, 12, 0, tzinfo=timezone.utc
                    ),
                ),
                Source(
                    name="JobSquare",
                    base_url="https://www.jobsquare.ma",
                    is_active=False,
                    last_run_at=None,
                ),
            ]
        )
        db.commit()

    def override_get_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            response = client.get("/api/sources")

        assert response.status_code == 200

        data = response.json()

        assert len(data) == 2
        assert data[0]["name"] == "JobSquare"
        assert data[0]["base_url"] == "https://www.jobsquare.ma"
        assert data[0]["is_active"] is False
        assert data[0]["last_run_at"] is None

        assert data[1]["name"] == "Stage.ma"
        assert data[1]["is_active"] is True
        assert data[1]["last_run_at"] is not None

    finally:
        app.dependency_overrides.clear()
        engine.dispose()

def test_get_stats():
    engine = create_test_database()

    with Session(engine) as db:
        source_stage = Source(
            name="Stage.ma",
            base_url="https://www.stage.ma",
            is_active=True,
        )

        source_job = Source(
            name="JobSquare",
            base_url="https://www.jobsquare.ma",
            is_active=True,
        )

        db.add_all([source_stage, source_job])
        db.commit()

        db.refresh(source_stage)
        db.refresh(source_job)

        db.add_all(
            [
                Offer(
                    source_id=source_stage.id,
                    title="Stage Data Scientist",
                    company="Company A",
                    location="Casablanca",
                    url="https://www.stage.ma/1",
                    fingerprint="stats-fingerprint-1",
                    first_seen_at=datetime(
                        2026, 10, 8, 10, 0, tzinfo=timezone.utc
                    ),
                ),
                Offer(
                    source_id=source_stage.id,
                    title="Stage Data Analyst",
                    company="Company B",
                    location="Rabat",
                    url="https://www.stage.ma/2",
                    fingerprint="stats-fingerprint-2",
                    first_seen_at=datetime(
                        2026, 10, 8, 11, 0, tzinfo=timezone.utc
                    ),
                ),
                Offer(
                    source_id=source_stage.id,
                    title="Stage Machine Learning",
                    company="Company C",
                    location="Fes",
                    url="https://www.stage.ma/3",
                    fingerprint="stats-fingerprint-3",
                    first_seen_at=datetime(
                        2026, 10, 7, 10, 0, tzinfo=timezone.utc
                    ),
                ),
                Offer(
                    source_id=source_job.id,
                    title="Stage Data Engineer",
                    company="Company D",
                    location="Rabat",
                    url="https://www.jobsquare.ma/1",
                    fingerprint="stats-fingerprint-4",
                    first_seen_at=datetime(
                        2026, 10, 6, 10, 0, tzinfo=timezone.utc
                    ),
                ),
            ]
        )

        db.commit()

    def override_get_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            response = client.get("/api/stats")

        assert response.status_code == 200

        data = response.json()

        # Vérifier les statistiques par source
        assert len(data["offers_by_source"]) == 2

        stage_stats = next(
            item
            for item in data["offers_by_source"]
            if item["source"] == "Stage.ma"
        )

        jobsquare_stats = next(
            item
            for item in data["offers_by_source"]
            if item["source"] == "JobSquare"
        )

        assert stage_stats["count"] == 3
        assert jobsquare_stats["count"] == 1

        # Vérifier les statistiques quotidiennes
        assert len(data["new_offers_by_day"]) == 7

        daily_counts = {
            item["date"]: item["count"]
            for item in data["new_offers_by_day"]
        }

        assert daily_counts["2026-10-08"] == 2
        assert daily_counts["2026-10-07"] == 1
        assert daily_counts["2026-10-06"] == 1

    finally:
        app.dependency_overrides.clear()
        engine.dispose()