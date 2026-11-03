# TeamAI

Projet TeamAI.

## Structure

- `registry/` : registre des agents
- `agents/` : définitions et implémentations des agents
- `board/` : tableau de bord et suivi
- `engine/` : moteur de documents (ORM, state machine, API HTTP)
- `tests/` : ensemble de tests (90 tests, unittest)
- `data/` : base de données SQLite et fichiers de logs

## Chemin officiel

Ce dépôt est la source de vérité du projet :

`/home/ubuntu/projects/teamai`

## Documentation

- `docs/contrat-agents.md` : contrat d’usage de l’équipe IA
- `docs/direction/` : recherche marché, canvas produit et validation
- `board/` : lectures et suivi de l’orchestrateur

---

# TeamAI API — Service HTTP

**TeamAI Engine HTTP API** : service REST minimal (stdlib Python, `http.server`) exposant une API de gestion de documents comptables :
création, lecture, liste et transition d'état. Persistance SQLite, authentification Bearer token.

## Fonctionnalités principales

| Fonctionnalité | Détails |
|---|---|
| Créer un document | `POST /documents` |
| Lister les documents | `GET /documents` (pagination `limit`/`offset`) |
| Lire un document | `GET /documents/{id}` |
| Transition d'état | `POST /documents/{id}/transition` |
| Santé du service | `GET /health` (sans authentification) |
| Authentification | Header `Authorization: Bearer <token>` (toutes les routes sauf `/health`) |

## Stack technique

- **Langage** : Python 3.12+ (stdlib uniquement : `http.server`, `sqlite3`, `json`)
- **Base de données** : SQLite (via `sqlite3` stdlib, `WAL`, `check_same_thread=False`)
- **Serveur HTTP** : `http.server.HTTPServer` + `BaseHTTPRequestHandler`
- **Authentification** : token Bearer (`Authorization: Bearer <token>`)
- **Déploiement** : `Dockerfile` (base `python:3.12-slim`) + `docker-compose.yml`
- **Tests** : `unittest` (standard library, 90 tests)

## Démarrer le service en local

```bash
# Créer la base
mkdir -p data
python3 -c "from engine.repository import DocumentRepository; DocumentRepository('data/teamai.db')"

# Démarrer avec un token
TEAMAI_TOKENS="tok_123" python3 -m engine.http --host 0.0.0.0 --port 8080 --db data/teamai.db
```

## Lancer les tests

```bash
# Tous les tests (90)
python3 -m unittest discover -s tests -v

# Avec l'option "error" sur les DeprecationWarning
python3 -W error::DeprecationWarning -m unittest discover -s tests -v
```

## Déployer avec Docker

```bash
# Build et lancement (conteneur)
TEAMAI_TOKENS="tok_123" docker compose up -d --build

# Vérifier
curl -s http://localhost:8080/health
docker compose ps
```

Variables d'environnement :

| Variable | Description | Exemple |
|---|---|---|
| `TEAMAI_DB_PATH` | Chemin vers la base SQLite | `/app/data/teamai.db` |
| `TEAMAI_TOKENS` | Liste des tokens valides (séparés par `,`) | `tok_123,dev-token` |
