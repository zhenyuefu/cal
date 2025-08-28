# Générateur d’abonnement calendrier (M1/M2 UFR Info)

Application Next.js pour composer un emploi du temps personnalisé à partir des calendriers officiels (ICS) des parcours M1/M2. Les données sont récupérées et normalisées par des scripts Python, puis exposées via une petite API qui retourne un flux ICS à s’abonner.

Le projet fonctionne entièrement en lecture locale des fichiers sous `data/` (ICS et JSON générés). Côté client, on choisit le semestre, le parcours, les UEs et les groupes pour obtenir un lien d’abonnement.

## Aperçu de l’architecture

- UI: Next.js + Mantine (`pages/`), lien d’abonnement généré dynamiquement.
- Données: scripts Python (`getcal.py`) qui téléchargent les ICS source et produisent des JSON normalisés.
- Backend (génération ICS à la volée): handlers Python (`api/gen*.py`) qui lisent les JSON et renvoient un calendrier filtré.

## Prérequis

- Node `>=22 <23` et/ou Bun `1.2.20`
- Python `3.9+`

## Installation

```bash
bun install   # ou: npm ci
```

## Mise à jour des calendriers (données locales)

1. Installer les dépendances Python et récupérer les calendriers:

```bash
pip install -r requirements.txt
python getcal.py
```

2. Ce script va:

- Télécharger les calendriers officiels (M1/M2) et filtrer les événements passés.
- Appliquer quelques corrections (ex: SFPN) si nécessaire.
- Écrire les fichiers suivants dans `data/`:
  - ICS sources: `M1_*.ics`, `M2_*.ics`
  - JSON par parcours/année (pour le backend): `M1_*.json`, `M2_*.json`
  - Catalogue des cours: `courses.json` (codes normalisés → libellé, parcours, nombre de groupes)
  - Index d’événements: `event_index.json` (métadonnées par UID) — utile pour le debug

Les codes de cours sont normalisés (ex: `MU5IN861` → `5IN861`). Les éléments particuliers comme `OIP`, `Anglais` sont traités.

## Lancer l’interface

```bash
bun run dev   # démarre Next.js sur http://localhost:3000
```

Ouvrez l’UI, choisissez:

- le semestre (S1/S2/S3),
- le parcours (AND, DAC, IMA, …),
- une ou plusieurs UEs (libellé lisible, valeur = code normalisé ex. `5IN861`),
- le groupe (détecté automatiquement depuis les données).

L’application génère un lien d’abonnement ICS que vous pouvez copier/ouvrir pour l’ajouter à votre agenda (iOS/Google: liens d’aide fournis dans la page).

## API de génération (flux ICS)

Trois handlers Python exposent les flux ICS filtrés:

- Semestre 1: `/api/gen`
- Semestre 2: `/api/gens2`
- Semestre 3: `/api/gens3`

Paramètres de requête (ex: `...?MAJ=AND&5IN861=1&5IN862=2`):

- `MAJ`: le parcours (AND, DAC, IMA, SESI, SFPN, …)
- paires `code=group`: chaque code d’UE normalisé (`5IN861`, `4IN202`, `OIP`, …) mappé à un numéro de groupe

Les handlers lisent exclusivement les JSON sous `data/` (pas de parsing ICS à la volée) et renvoient un calendrier ICS prêt à l’emploi.

Remarque: en développement local, ces endpoints Python sont destinés à un déploiement serverless (ex: Vercel) ou à un serveur Python dédié. L’UI locale reste pleinement fonctionnelle si les fichiers `data/*.json` sont présents.

## Commandes utiles

- Dev: `bun run dev`
- Build: `bun run build`
- Start: `bun run start`
- Lint: `bun run lint`
- MAJ des données: `pip install -r requirements.txt && python getcal.py`

## Structure du projet

- `pages/`: pages Next.js (`_app.tsx`, `index.tsx`, …)
- `data/`: ICS/JSON générés (ne pas éditer à la main)
- `api/`: scripts Python (récupération et handlers)
- `public/`, `styles/`: assets et styles
- `.github/workflows/`: automatisation (MAJ des calendriers)

## Conseils & sécurité

- Ne pas committer de secrets. Les variables visibles côté client doivent être préfixées `NEXT_PUBLIC_*`.
- Respecter Node/Bun/Python aux versions indiquées pour éviter les surprises.

## Dépannage

- Pas d’UE dans la liste: relancez `python getcal.py` pour régénérer `data/courses.json`.
- Groupes incorrects: vérifiez que vos ICS sont à jour et que les `*.json` ont bien été régénérés.
- Lien d’abonnement vide: assurez-vous que l’API déployée lit bien les JSON `data/M*_*.json` et `courses.json`.
