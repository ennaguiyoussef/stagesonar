"""Envoi des e-mails récapitulatifs aux abonnés."""

import html
import smtplib
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Notification, Offer, Subscriber


def send_digest(
    db: Session,
    subscriber: Subscriber,
    scored_offers: list[tuple[Offer, float]],
) -> None:
    """Envoie un e-mail avec les nouvelles offres d'un abonné.

    Les offres déjà envoyées à cet abonné sont ignorées.
    Après un envoi SMTP réussi, une notification est créée pour
    chaque offre envoyée.
    """

    if not scored_offers:
        return

    offer_ids = [offer.id for offer, _score in scored_offers]

    already_notified = {
        offer_id
        for offer_id, in db.query(Notification.offer_id)
        .filter(
            Notification.subscriber_id == subscriber.id,
            Notification.offer_id.in_(offer_ids),
        )
        .all()
    }

    new_offers = [
        (offer, score)
        for offer, score in scored_offers
        if offer.id not in already_notified
    ]

    if not new_offers:
        return

    unsubscribe_url = (
        f"{settings.frontend_url}/unsubscribe/"
        f"{subscriber.unsubscribe_token}"
    )

    html_items = []

    for offer, _score in new_offers:
        title = html.escape(offer.title)
        company = html.escape(offer.company or "Non spécifiée")
        location = html.escape(offer.location or "Non spécifiée")
        url = html.escape(offer.url, quote=True)

        html_items.append(
            f"""
            <li>
                <strong>{title}</strong><br>
                Entreprise : {company}<br>
                Ville : {location}<br>
                <a href="{url}">Voir l'offre</a>
            </li>
            """
        )

    subject = f"{len(new_offers)} nouvelles offres de stage pour vous"

    html_body = f"""
    <html>
        <body>
            <h2>{html.escape(subject)}</h2>

            <ul>
                {''.join(html_items)}
            </ul>

            <hr>

            <p>
                <a href="{html.escape(unsubscribe_url, quote=True)}">
                    Se désinscrire
                </a>
            </p>
        </body>
    </html>
    """

    text_items = []

    for offer, _score in new_offers:
        text_items.append(
            f"- {offer.title}\n"
            f"  Entreprise : {offer.company or 'Non spécifiée'}\n"
            f"  Ville : {offer.location or 'Non spécifiée'}\n"
            f"  Lien : {offer.url}"
        )

    text_body = (
        f"{subject}\n\n"
        + "\n\n".join(text_items)
        + f"\n\nSe désinscrire : {unsubscribe_url}"
    )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.mail_from
    message["To"] = subscriber.email
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(message)

    for offer, score in new_offers:
        db.add(
            Notification(
                subscriber_id=subscriber.id,
                offer_id=offer.id,
                score=score,
            )
        )

    db.commit()
