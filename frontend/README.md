# Frontend StageSonar

Site React (Vite, TypeScript, Tailwind) qui affiche les offres collectées par le backend.

## Démarrage

Le backend doit tourner sur http://localhost:8000 (voir le README à la racine).

```bash
cd frontend
npm install
npm run dev
```

Le site est alors sur http://localhost:5173. Si l'API tourne ailleurs, copier
`.env.example` en `.env` et modifier `VITE_API_URL`.

## Organisation

```
src/
├── main.tsx          point d'entrée, active le routeur
├── App.tsx           navigation commune et déclaration des pages
├── index.css         Tailwind + couleurs et polices de StageSonar
├── api/client.ts     une fonction par route de l'API
└── pages/
    ├── Home.tsx      accueil
    ├── Offers.tsx    liste des offres : recherche, filtres, pagination
    └── Subscribe.tsx formulaire d'abonnement (carte J6)
```
