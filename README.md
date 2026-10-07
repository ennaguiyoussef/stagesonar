# StageSonar

Application web qui surveille plusieurs sites de stages, repère les offres qui
viennent d'être publiées et envoie à chaque abonné celles qui correspondent à
son profil. Projet de web mining réalisé en binôme par Youssef et Fouad.

## Fonctionnement

1. Un planificateur lance le pipeline toutes les six heures.
2. Un scraper par site collecte les offres dans un format commun.
3. Une empreinte SHA-256 (titre + entreprise + ville) permet de reconnaître les offres déjà vues.
4. Les nouvelles offres sont comparées aux profils des abonnés par TF-IDF.
5. Chaque abonné concerné reçoit un e-mail récapitulatif.

## Stack

| Couche | Outil |
|---|---|
| Backend | FastAPI, SQLAlchemy, Pydantic |
| Scraping | httpx, BeautifulSoup |
| Planification | APScheduler |
| Base | PostgreSQL (SQLite par défaut en développement) |
| Matching | scikit-learn (TF-IDF) |
| Frontend | React, TypeScript, Vite, Tailwind |

## Démarrage

```bash
git clone https://github.com/ennaguiyoussef/stagesonar.git
cd stagesonar
cp .env.example .env

cd backend
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

L'API répond sur http://localhost:8000/health et sa documentation interactive
est sur http://localhost:8000/docs.

Sans configuration, l'application crée un fichier SQLite local. Pour utiliser
PostgreSQL, lancer `docker compose up -d db` à la racine puis décommenter
`DATABASE_URL` dans `.env`.

## Tests

```bash
cd backend
pytest
```

## Arborescence

```
stagesonar/
├── backend/
│   ├── app/
│   │   ├── main.py          API et cycle de vie
│   │   ├── config.py        variables d'environnement
│   │   ├── database.py      session SQLAlchemy
│   │   ├── models.py        les cinq tables
│   │   ├── schemas.py       modèles Pydantic
│   │   ├── routers/         offers, subscribers, admin
│   │   ├── scrapers/        base + un module par site
│   │   └── services/        dedup, matcher, notifier, pipeline
│   ├── tests/
│   └── requirements.txt
├── frontend/
├── docker-compose.yml
└── .env.example
```

## Répartition

| Qui | Périmètre |
|---|---|
| Youssef | Base de données, scraper du site A, détection des nouveautés, scheduler, matching, pipeline, Docker |
| Fouad | Scraper du site B, API (offres, sources, abonnés), e-mails, frontend |
| Ensemble | Choix des sites, test de bout en bout, README final, démonstration |

Le détail des tâches est sur le tableau Trello du projet.

## Règles de travail

- Personne ne pousse directement sur `main`.
- Une tâche Trello = une branche = une pull request.
- Nom de branche : `feat/scraper-site-a`, `feat/api-offres`, `fix/...`.
- L'autre membre du binôme relit la pull request avant la fusion.
- `pytest` doit passer avant d'ouvrir la pull request.
- Le fichier `.env` ne va jamais sur GitHub.

## Règles de collecte

- Lire le `robots.txt` de chaque site et ne collecter que les pages autorisées.
- Au moins deux secondes entre deux requêtes, avec un User-Agent explicite.
- Ne stocker que les informations publiques de l'offre et renvoyer vers la page d'origine.
