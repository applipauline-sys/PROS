# MORNY IMMOBILIER — Prospection

Application personnelle et locale. Cette première étape prépare uniquement l’architecture, la navigation et le stockage. Les modules de biens, calendrier, zones, statistiques, import/export et sauvegardes ne sont pas encore implémentés. Aucune donnée fictive ni coordonnée de propriétaire n’est enregistrée.

## Installation

Prérequis : Python 3.12 et Node.js 22 ou 24 avec npm. Une connexion Internet est nécessaire uniquement pour installer les dépendances. Aucun compte, hébergement ni clé API n’est requis.

Sous Linux/macOS, depuis le dossier du projet :

```bash
bash scripts/install.sh
```

Sous Windows (PowerShell, Python et Node installés) :

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend\requirements.lock.txt
npm --prefix frontend ci
npm --prefix frontend run build
cd backend
..\.venv\Scripts\python.exe -m alembic upgrade head
cd ..
```

Windows et macOS n’ont pas été testés dans cet environnement Linux.

## Utilisation quotidienne, hors ligne

```bash
python demarrer.py
```

Sous Windows : `py demarrer.py`. Ouvrir l’adresse locale indiquée dans le terminal. Garder ce terminal ouvert. Pour arrêter, appuyer sur **Ctrl+C**. L’application écoute exclusivement sur `127.0.0.1:8000`. Aucun CDN, police distante, télémétrie ou service OpenAI n’est utilisé. Les dépendances et ressources graphiques sont installées localement.

La page **Paramètres** et l’indicateur en bas de page affichent le résultat du contrôle réel de l’API et de SQLite. Les autres pages présentent clairement leur état de préparation, sans simuler des fonctions métier.

## Architecture

- `frontend/src/main.tsx` : interface React/TypeScript et navigation par URL fragment, sans rechargement.
- `frontend/src/style.css` : styles locaux, palette sobre, adaptation aux petits écrans, focus clavier et mouvements réduits.
- `backend/app/main.py` : API FastAPI et distribution de l’interface compilée.
- `backend/app/database.py` : moteur SQLAlchemy et répertoire de données.
- `backend/migrations/` : migrations Alembic. La révision `0001` initialise le suivi ; aucune table métier n’est créée à ce stade.
- `backend/tests/` : test de migrations répétables, connexion SQLite et état API avec stockage temporaire.
- `scripts/install.sh` : installation et compilation.
- `demarrer.py` : migrations puis démarrage local.

Le CSS est écrit directement pour garder ce socle visuel léger ; Tailwind et les bibliothèques métier pourront être ajoutés lorsqu’ils seront utiles. Aucun logo officiel n’a été inventé.

## Données

SQLite est enregistré dans `data/morny.sqlite3`, hors suivi Git. `MORNY_DATA_DIR` permet de choisir un autre dossier local (chemin absolu recommandé). Les futures photos et sauvegardes devront rester locales. Ne pas supprimer `data/`. Les migrations sont appliquées au lancement ; ne jamais modifier une migration déjà utilisée. Avant de futures évolutions contenant des données réelles, prévoir une sauvegarde. La fonction de sauvegarde/restauration sera développée ultérieurement.

## Développement

Utiliser le checkout existant : chaque tâche cloud est déjà isolée, aucun worktree supplémentaire n’est nécessaire.

```bash
# Terminal 1, à la racine
cd backend
../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# Terminal 2, à la racine
npm --prefix frontend run dev
```

Vite utilise une adresse de boucle locale et relaie `/api` vers FastAPI. Pour refléter les modifications dans le lanceur quotidien, relancer `npm --prefix frontend run build` puis redémarrer l’application.

```bash
.venv/bin/python -m pytest backend/tests -q
npm --prefix frontend run build
```

## Prochaine étape

Attendre les instructions suivantes avant d’implémenter les fonctions métier. La liste détaillée des neuf zones et communes n’a pas été fournie et sera nécessaire à leur intégration.
