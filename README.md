# MORNY IMMOBILIER — Prospection

Application personnelle et locale. Le module « Mes biens » permet de créer, consulter, rechercher, modifier et supprimer les fiches avec leurs photos locales. Le calendrier, les statistiques, les actions groupées, les imports/exports et les sauvegardes restent à développer. Aucune donnée fictive ni coordonnée de propriétaire n’est enregistrée.

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
python3 demarrer.py
```

Sous Windows : `py demarrer.py`. Ouvrir l’adresse locale indiquée dans le terminal. Garder ce terminal ouvert. Pour arrêter, appuyer sur **Ctrl+C**. L’application écoute exclusivement sur `127.0.0.1:8000`. Aucun CDN, police distante, télémétrie ou service OpenAI n’est utilisé. Les dépendances et ressources graphiques sont installées localement.

La page **Paramètres** et l’indicateur en bas de page affichent le résultat du contrôle réel de l’API et de SQLite. La page « Mes biens » est fonctionnelle. Les pages des autres modules présentent leur état de préparation, sans simuler des fonctions métier.

## Architecture

- `frontend/src/main.tsx` : interface React/TypeScript et navigation par URL fragment, sans rechargement.
- `frontend/src/style.css` : styles locaux, palette sobre, adaptation aux petits écrans, focus clavier et mouvements réduits.
- `backend/app/main.py` : API FastAPI et distribution de l’interface compilée.
- `backend/app/database.py` : moteur SQLAlchemy et répertoire de données.
- `backend/migrations/` : migrations Alembic. La révision `0001` initialise le suivi ; `0002` ajoute les biens, les photos et l’historique. Le lanceur applique automatiquement les migrations sans réinitialiser les données.
- `backend/tests/` : tests des migrations répétables, du CRUD, des champs facultatifs, de la recherche, des filtres, des zones, des photos et de la persistance avec stockage temporaire.
- `backend/app/config/zones.json` : correspondances exactes des neuf zones, communes et couleurs.
- `frontend/src/Properties.tsx` et `PropertyForm.tsx` : tableau de gestion, consultation et formulaire.
- `backend/app/properties.py`, `schemas.py`, `models.py`, `photos.py` : API, validations, modèle de données et images locales.
- `scripts/install.sh` : installation et compilation.
- `demarrer.py` : migrations puis démarrage local.

Le CSS est écrit directement pour garder ce socle visuel léger ; Tailwind et les bibliothèques métier pourront être ajoutés lorsqu’ils seront utiles. Aucun logo officiel n’a été inventé.

## Données

SQLite est enregistré dans `data/morny.sqlite3`, hors suivi Git. `MORNY_DATA_DIR` permet de choisir un autre dossier local (chemin absolu recommandé). Les photos sont dans `data/photos/`, liées aux fiches par identifiant et clé étrangère SQLite. Ce dossier doit être conservé avec la base. Ne pas supprimer `data/`. Les migrations sont appliquées au lancement ; ne jamais modifier une migration déjà utilisée. Avant de futures évolutions contenant des données réelles, prévoir une sauvegarde. La fonction de sauvegarde/restauration sera développée ultérieurement.

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

## Utiliser « Mes biens »

1. Ouvrir **Mes biens**, puis **Ajouter un bien**. Aucun renseignement immobilier n’est obligatoire ; le statut initial est « Non prospecté ».
2. Rechercher une commune, puis la sélectionner dans la liste alphabétique. Pour une autre commune, sélectionner **Autre ville** et saisir son nom. La zone est calculée immédiatement puis vérifiée par le serveur à l’enregistrement.
3. Renseigner, si connus, la surface, le DPE, le GES, la source, les notes et la prochaine action. Le nom de l’agence apparaît uniquement pour la source « Agence immobilière ». Les dates de création et modification sont automatiques.
4. Une photo JPEG ou PNG de 5 Mo maximum peut être ajoutée. Elle est vérifiée, orientée, convertie en JPEG (2 000 pixels maximum de côté), et ses métadonnées sont retirées. Aucun envoi à un service externe. Les formats HEIC/SVG ne sont pas acceptés : exporter une photo HEIC en JPEG avant de la choisir.
5. Cliquer sur **Enregistrer**, puis sur une ligne du tableau pour consulter la fiche et son historique. **Modifier la fiche** permet de changer tous les renseignements, remplacer ou retirer la photo. Une confirmation est demandée avant la modification d’une fiche existante et avant sa suppression.
6. Utiliser la recherche par adresse, ville, source ou agence. Le bouton **Filtres** propose ville exacte, zone, source et statut, combinables avec la recherche. Les tris portent sur la ville, la zone, les dates et le statut. Pagination : 10, 25, 50 ou 100 biens par page. Les cases sélectionnent les lignes, sans appliquer d’actions groupées à cette étape.

Ne jamais saisir de coordonnées de propriétaire dans les notes ou l’adresse. L’application ne comporte aucun champ de contact.

### Conservation et suppression

La suppression retire le bien des listes et de la recherche ; c’est une **suppression logique**. La fiche, ses versions et les anciennes photos restent localement pour éviter une perte irréversible. La restauration depuis l’interface et la purge définitive ne font pas partie de ce module. Annuler un formulaire après téléversement peut laisser une photo non rattachée : elle reste uniquement dans le dossier local et n’est jamais envoyée ailleurs. Aucune purge automatique n’est effectuée.

Chaque enregistrement et son instantané d’historique sont transactionnels. Un numéro de version empêche un onglet ancien d’écraser une fiche modifiée dans un autre onglet : en cas de conflit, fermer puis rouvrir la fiche avant de reprendre la modification.

### Modifier les zones

Éditer `backend/app/config/zones.json`, puis redémarrer le serveur. La ville est comparée sans tenir compte de la casse, des accents et des espaces superflus. Les villes inconnues sont « Hors zone ». La zone n’est pas dupliquée en base : un changement de configuration est donc reflété dans les fiches, la recherche, les filtres et le tri dès le redémarrage. Les anciens instantanés d’historique restent inchangés.

### Vérification dans un navigateur

Le script `scripts/test_browser.py` utilise une base et des photos temporaires, démarre/arrête son propre serveur sur une adresse de boucle locale, puis teste les parcours réels. Il nécessite Python avec Playwright et Pillow, ainsi que Chromium (ou le navigateur Chromium installé par Playwright). Il peut être exécuté avec `python3 scripts/test_browser.py` depuis la racine. Il ne crée aucune donnée de démonstration dans la base de production. Le test a été exécuté sous Linux ; macOS et Windows n’ont pas été validés ici.

## Prochaine étape

Les autres modules seront développés à votre prochaine instruction. La page « Zones de prospection » reste un espace réservé ; les neuf zones sont déjà actives dans « Mes biens ».
