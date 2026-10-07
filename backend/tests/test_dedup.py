from app.services.dedup import compute_fingerprint


def test_same_offer_on_two_sites_gives_same_fingerprint():
    a = compute_fingerprint("Stage Data Scientist", "Société Générale", "Casablanca")
    b = compute_fingerprint("  stage data scientist ", "SOCIETE GENERALE", "casablanca.")
    assert a == b


def test_different_offers_give_different_fingerprints():
    a = compute_fingerprint("Stage Data Scientist", "Oracle", "Casablanca")
    b = compute_fingerprint("Stage Data Engineer", "Oracle", "Casablanca")
    assert a != b
