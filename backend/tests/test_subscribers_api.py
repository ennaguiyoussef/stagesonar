from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Subscriber


def create_test_database():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


def test_subscribe():
    engine = create_test_database()

    def override_get_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/subscribers",
                json={
                    "email": "fouad@example.com",
                    "keywords": "data, machine learning",
                    "location": "France",
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert data["message"] == "Abonnement enregistré."
        assert data["unsubscribe_token"]

        with Session(engine) as db:
            subscriber = db.query(Subscriber).first()

            assert subscriber is not None
            assert subscriber.email == "fouad@example.com"
            assert subscriber.keywords == "data, machine learning"
            assert subscriber.location == "France"
            assert subscriber.is_active is True
            assert subscriber.unsubscribe_token == data["unsubscribe_token"]

    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_double_subscribe_same_email():
    engine = create_test_database()

    def override_get_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            first_response = client.post(
                "/api/subscribers",
                json={
                    "email": "fouad@example.com",
                    "keywords": "python",
                    "location": "France",
                },
            )

            first_token = first_response.json()["unsubscribe_token"]

            second_response = client.post(
                "/api/subscribers",
                json={
                    "email": "fouad@example.com",
                    "keywords": "machine learning, data science",
                    "location": "Germany",
                },
            )

        assert first_response.status_code == 200
        assert second_response.status_code == 200

        second_token = second_response.json()["unsubscribe_token"]

        with Session(engine) as db:
            subscribers = db.query(Subscriber).all()

            assert len(subscribers) == 1

            subscriber = subscribers[0]

            assert subscriber.email == "fouad@example.com"
            assert subscriber.keywords == "machine learning, data science"
            assert subscriber.location == "Germany"
            assert subscriber.is_active is True
            assert subscriber.unsubscribe_token == first_token
            assert second_token == first_token

    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_unsubscribe():
    engine = create_test_database()

    def override_get_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            subscribe_response = client.post(
                "/api/subscribers",
                json={
                    "email": "fouad@example.com",
                    "keywords": "data",
                    "location": "France",
                },
            )

            token = subscribe_response.json()["unsubscribe_token"]

            response = client.delete(
                f"/api/subscribers/{token}"
            )

        assert response.status_code == 200
        assert response.json()["message"] == "Désinscription effectuée."

        with Session(engine) as db:
            subscriber = db.query(Subscriber).first()

            assert subscriber is not None
            assert subscriber.is_active is False

    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_unsubscribe_unknown_token():
    engine = create_test_database()

    def override_get_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            response = client.delete(
                "/api/subscribers/token-inconnu"
            )

        assert response.status_code == 404

    finally:
        app.dependency_overrides.clear()
        engine.dispose()