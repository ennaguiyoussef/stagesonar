"""Matching entre les nouvelles offres et les profils des abonnés.

Chaque texte (offre ou mots-clés d'un abonné) devient un vecteur TF-IDF : un mot
pèse lourd s'il est fréquent dans ce texte et rare dans les autres. La similarité
cosinus entre deux vecteurs vaut 0 quand les textes n'ont aucun mot en commun et
se rapproche de 1 quand ils parlent de la même chose.
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings
from app.models import Offer, Subscriber
from app.services.dedup import normalize

# Mots présents dans presque toutes les offres : ils ne disent rien du profil recherché.
STOP_WORDS = [
    "stage", "stages", "stagiaire", "stagiaires", "offre", "poste", "h", "f",
    "de", "des", "du", "d", "la", "le", "les", "l", "un", "une", "et", "en", "au", "aux", "pour", "a",
]


def match_offers(offers: list[Offer], subscribers: list[Subscriber]) -> dict[int, list[tuple[Offer, float]]]:
    """Renvoie, pour chaque abonné concerné, ses offres retenues avec leur score (meilleur score en premier)."""
    if not offers or not subscribers:
        return {}

    offer_texts = [f"{o.title} {o.company} {o.description}" for o in offers]
    profile_texts = [s.keywords for s in subscribers]

    # Le vocabulaire et les poids sont appris sur l'ensemble des textes du lot.
    vectorizer = TfidfVectorizer(strip_accents="unicode", stop_words=STOP_WORDS)
    vectors = vectorizer.fit_transform(offer_texts + profile_texts)
    # scores[i][j] = similarité entre l'abonné i et l'offre j
    scores = cosine_similarity(vectors[len(offers):], vectors[: len(offers)])

    matches = {}
    for subscriber, row in zip(subscribers, scores):
        city = normalize(subscriber.location)
        kept = [
            (offer, round(float(score), 3))
            for offer, score in zip(offers, row)
            if score >= settings.match_threshold and city in normalize(offer.location)
        ]
        if kept:
            matches[subscriber.id] = sorted(kept, key=lambda pair: pair[1], reverse=True)
    return matches