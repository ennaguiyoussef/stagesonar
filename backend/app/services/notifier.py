"""Envoi des e-mails récapitulatifs aux abonnés."""

import html
import smtplib
from email.message import EmailMessage

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Notification, Offer, Subscriber

# Un e-mail ne peut pas charger de feuille de style : chaque balise porte son propre style.
FONT = "font-family:'Segoe UI',Helvetica,Arial,sans-serif"
ABYSS, WATER, FOAM, SLATE, LINE, SONAR, BEACON = "#0B2540", "#E8F1F2", "#FBFDFD", "#516676", "#C4D6DA", "#0B6E6C", "#F5A300"


def offer_html(offer: Offer) -> str:
    """Bloc HTML d'une offre : titre, entreprise, lieu, bouton."""
    details = "".join(
        f'<p style="margin:4px 0 0;font-size:15px;color:{color}">{html.escape(value)}</p>'
        for value, color in ((offer.company, ABYSS), (offer.location, SLATE))
        if value
    )
    return f"""
    <tr><td style="padding:20px 24px;border-top:1px solid {LINE}">
      <p style="margin:0;font-size:18px;line-height:1.35;font-weight:700;color:{ABYSS}">{html.escape(offer.title)}</p>
      {details}
      <p style="margin:16px 0 0">
        <a href="{html.escape(offer.url, quote=True)}" style="display:inline-block;background:{ABYSS};color:{FOAM};font-size:15px;font-weight:600;text-decoration:none;padding:10px 18px;border-radius:6px">Voir l'offre</a>
      </p>
    </td></tr>"""


def build_email(subscriber: Subscriber, offers: list[Offer]) -> tuple[str, str, str]:
    """Renvoie l'objet, la version texte et la version HTML de l'e-mail."""
    count = len(offers)
    subject = "1 nouvelle offre de stage pour vous" if count == 1 else f"{count} nouvelles offres de stage pour vous"
    unsubscribe_url = f"{settings.frontend_url}/unsubscribe/{subscriber.unsubscribe_token}"

    text_body = f"{subject}\n\n" + "\n\n".join(
        "\n".join(line for line in (offer.title, offer.company, offer.location, offer.url) if line) for offer in offers
    ) + f"\n\nSe désinscrire : {unsubscribe_url}"

    html_body = f"""<html>
<body style="margin:0;padding:24px 12px;background:{WATER};{FONT}">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;margin:0 auto;background:{FOAM};border:1px solid {LINE};border-radius:10px;overflow:hidden;{FONT}">
    <tr><td style="background:{ABYSS};padding:18px 24px;color:{FOAM};font-size:22px;font-weight:700">
      <span style="color:{BEACON}">&#9679;</span> StageSonar
    </td></tr>
    <tr><td style="padding:24px 24px 20px">
      <h1 style="margin:0;font-size:24px;line-height:1.25;color:{ABYSS}">{subject}</h1>
      <p style="margin:10px 0 0;font-size:15px;line-height:1.5;color:{SLATE}">Sélection établie à partir de vos mots-clés : <strong style="color:{ABYSS}">{html.escape(subscriber.keywords)}</strong>.</p>
    </td></tr>
    {''.join(offer_html(offer) for offer in offers)}
    <tr><td style="padding:18px 24px;background:{WATER};border-top:1px solid {LINE};font-size:13px;line-height:1.5;color:{SLATE}">
      Vous recevez cet e-mail car vous êtes abonné aux alertes StageSonar.
      <a href="{html.escape(unsubscribe_url, quote=True)}" style="color:{SONAR}">Se désinscrire</a>
    </td></tr>
  </table>
</body>
</html>"""
    return subject, text_body, html_body


def send_digest(db: Session, subscriber: Subscriber, scored_offers: list[tuple[Offer, float]]) -> None:
    """Envoie à un abonné un e-mail avec ses nouvelles offres, puis enregistre chaque envoi.

    Les offres déjà envoyées à cet abonné sont ignorées.
    """
    offer_ids = [offer.id for offer, _score in scored_offers]
    already_notified = set(
        db.scalars(
            select(Notification.offer_id).where(
                Notification.subscriber_id == subscriber.id, Notification.offer_id.in_(offer_ids)
            )
        )
    )
    new_offers = [(offer, score) for offer, score in scored_offers if offer.id not in already_notified]
    if not new_offers:
        return

    subject, text_body, html_body = build_email(subscriber, [offer for offer, _score in new_offers])
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

    db.add_all(Notification(subscriber_id=subscriber.id, offer_id=offer.id, score=score) for offer, score in new_offers)
    db.commit()