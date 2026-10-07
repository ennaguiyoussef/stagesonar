"""Matching entre les nouvelles offres et les profils des abonnés (TF-IDF + cosinus)."""

# TODO (jour 4) : match_offers(offers, subscribers) -> dict[int, list[tuple[Offer, float]]]
# Clé : id de l'abonné. Valeur : les offres retenues avec leur score,
# c'est-à-dire celles dont la similarité dépasse settings.match_threshold.
