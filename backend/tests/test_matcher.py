from app.models import Offer, Subscriber
from app.services.matcher import match_offers


def make_offer(id: int, title: str, description: str = "", location: str = "Casablanca") -> Offer:
    return Offer(id=id, title=title, company="Entreprise", location=location, description=description, url="u")


def make_subscriber(id: int, keywords: str, location: str = "") -> Subscriber:
    return Subscriber(id=id, email=f"abonne{id}@exemple.ma", keywords=keywords, location=location)


OFFERS = [
    make_offer(1, "Stage Data Scientist", "Python, machine learning et analyse de données"),
    make_offer(2, "Stagiaire Marketing digital", "Communication, réseaux sociaux et contenu"),
    make_offer(3, "Stage Comptabilité", "Saisie comptable et rapprochements bancaires"),
]


def test_each_profile_only_gets_its_own_offers():
    data = make_subscriber(1, "data science, python, machine learning")
    marketing = make_subscriber(2, "marketing, communication, réseaux sociaux")
    matches = match_offers(OFFERS, [data, marketing])
    assert [offer.id for offer, _ in matches[1]] == [1]
    assert [offer.id for offer, _ in matches[2]] == [2]


def test_subscriber_without_any_match_is_absent():
    assert match_offers(OFFERS, [make_subscriber(1, "droit, juridique, contentieux")]) == {}


def test_accents_and_case_do_not_matter():
    matches = match_offers(OFFERS, [make_subscriber(1, "COMPTABILITE")])
    assert [offer.id for offer, _ in matches[1]] == [3]


def test_city_filter_uses_contains():
    offers = [
        make_offer(1, "Stage marketing digital", location="Guéliz, Marrakech"),
        make_offer(2, "Stage marketing digital", location="Fès, Fès-Meknès"),
    ]
    matches = match_offers(offers, [make_subscriber(1, "marketing digital", location="marrakech")])
    assert [offer.id for offer, _ in matches[1]] == [1]


def test_generic_word_stage_alone_matches_nothing():
    assert match_offers(OFFERS, [make_subscriber(1, "stage")]) == {}


def test_empty_inputs():
    assert match_offers([], [make_subscriber(1, "python")]) == {}
    assert match_offers(OFFERS, []) == {}
