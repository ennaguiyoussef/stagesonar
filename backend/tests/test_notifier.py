from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Notification, Offer, Source, Subscriber
from app.services.notifier import send_digest


def create_test_database():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


def test_send_digest_creates_notifications_and_does_not_resend():
    engine = create_test_database()

    try:
        with Session(engine) as db:
            source = Source(
                name="Site test",
                base_url="https://exemple.ma",
                is_active=True,
            )
            db.add(source)
            db.commit()
            db.refresh(source)

            subscriber = Subscriber(
                email="fouad@example.com",
                keywords="data, machine learning",
                location="France",
                is_active=True,
                unsubscribe_token="test-token",
            )
            db.add(subscriber)
            db.commit()
            db.refresh(subscriber)

            offer_1 = Offer(
                source_id=source.id,
                title="Stage Data Scientist",
                company="Company A",
                location="Casablanca",
                url="https://exemple.ma/data-scientist",
                fingerprint="notifier-fingerprint-1",
            )

            offer_2 = Offer(
                source_id=source.id,
                title="Stage Data Analyst",
                company="Company B",
                location="Rabat",
                url="https://exemple.ma/data-analyst",
                fingerprint="notifier-fingerprint-2",
            )

            db.add_all([offer_1, offer_2])
            db.commit()
            db.refresh(offer_1)
            db.refresh(offer_2)

            scored_offers = [
                (offer_1, 0.95),
                (offer_2, 0.82),
            ]

            with patch("app.services.notifier.smtplib.SMTP") as mock_smtp:
                smtp = mock_smtp.return_value.__enter__.return_value

                send_digest(db, subscriber, scored_offers)

                assert mock_smtp.call_count == 1
                smtp.starttls.assert_called_once()
                smtp.login.assert_called_once()
                smtp.send_message.assert_called_once()

            notifications = db.query(Notification).all()

            assert len(notifications) == 2

            sent_offer_ids = {
                notification.offer_id
                for notification in notifications
            }

            assert sent_offer_ids == {offer_1.id, offer_2.id}

            with patch("app.services.notifier.smtplib.SMTP") as mock_smtp:
                send_digest(db, subscriber, scored_offers)

                mock_smtp.assert_not_called()

            notifications = db.query(Notification).all()

            assert len(notifications) == 2

    finally:
        engine.dispose()