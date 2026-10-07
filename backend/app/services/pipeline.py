"""Orchestration : collecte -> détection des nouveautés -> matching -> notification."""

# TODO (jour 5) : run_pipeline() -> dict
# 1. Pour chaque scraper actif : fetch_offers() puis save_new_offers()
# 2. match_offers() sur les nouvelles offres
# 3. send_digest() pour chaque abonné concerné
# 4. Mettre à jour scrape_runs et sources.last_run_at
