# CHANGELOG.md — Historique des versions

## v1.0.0 — 2026-11-03

### Ajouts

- **Architecture** : documentation `ARCHITECTURE.md` (modules, flux HTTP, état du document, rôles des classes)
- **API** : documentation `API.md` (endpoints, auth, corps de requête, réponses, exemples curl)
- **Runbook** : documentation `RUNBOOK.md` (démarrage nohup, arrêt, logs, rotation de token, backup)
- **Dépannage** : documentation `TROUBLESHOOTING.md` (curl 000, 401, 500, port occupé, base corrompue)
- **Contribution** : documentation `CONTRIBUTING.md` (branches, commits, règles de tests)
- **Conteneurisation** : `Dockerfile` (base python:3.12-slim), `docker-compose.yml`, `.dockerignore`
- **Entrée server** : `engine/http.py` — point d'entrée `python3 -m engine.http` avec `argparse` (`--host`, `--port`, `--db`)
- **Authentification** : `TEAMAI_TOKENS` obligatoire au démarrage (refus de lancer sans token)

### Corrections

- LSP diagnostic Pyright `Cannot access attribute "store" for class "BaseServer"` → `make_app(store)` définit `_HttpHandler.store = store` (class attribute)

### Tests

- 90 tests unitaires (`unittest`, stdlib) — `python3 -m unittest discover -s tests -v`
- Aucun `DeprecationWarning` — `python3 -W error::DeprecationWarning -m unittest discover -s tests -v` → OK

---

## Revue approfondie des commits majeurs (ordre chronologique)

| Commit | Branche | Description |
|---|---|---|
| `9c931b8` | `persistence-sqlite` | Couche SQLite repository (`DocumentRepository`) |
| `1ef739e` | `http-api` | API HTTP minimale (`engine/http.py`). 169 tests |
| `afef914` | merge `http-api` | Merge de l'API HTTP |
| `ebd0de7` | `ci-github-actions` | GitHub Actions CI (`.github/workflows/tests.yml`). 46 tests |
| `9c0b76a` | merge `ci-github-actions` | Merge de la CI |
| `2440384` | `business-validation` | Règles métier `engine/validation.py`. 59 tests |
| `7dac68c` | merge `business-validation` | Merge de la validation |
| `d6510d5` | `api-authentication` | Authentification Bearer (`engine/auth.py`). 70 tests |
| `694a970` | merge `api-authentication` | Merge de l'authentification |
| `6fddd95` | `openapi-docs` | Spécification OpenAPI `docs/openapi.yaml`, guide `docs/technique/05-http-api.md` |
| `56ca14b` | merge `openapi-docs` | Merge de la doc OpenAPI |
| `996e09f` | `docker-deployment` | Dockerfile, docker-compose.yml, .dockerignore |
| `e56ebe4` | merge `docker-deployment` | Merge du déploiement Docker |

---

## Historique par lot

| Lot | Branche | Commit final | Tests |
|---|---|---|---|
| Persistence SQLite | `persistence-sqlite` | `9c931b8` | 35 |
| HTTP API minimale | `http-api` | `1ef739e` | 169 |
| CI GitHub Actions | `ci-github-actions` | `ebd0de7` | 46 |
| Business Validation | `business-validation` | `2440384` | 59 |
| API Authentication | `api-authentication` | `d6510d5` | 70 |
| OpenAPI Docs | `openapi-docs` | `6fddd95` | 90 |
| Docker Deployment | `docker-deployment` | `996e09f` | 90 |

---

## Notes de version par lot

### `persistence-sqlite` (`9c931b8`)

- Couche SQLite avec `DocumentRepository` (`save`, `get`, `list`)
- `check_same_thread=False`, `PRAGMA journal_mode=WAL`
- Fix Python 3.12 `DeprecationWarning` sur l'adaptateur `datetime`
- 35 tests

### `http-api` (`1ef739e`)

- API REST minimale : `POST /documents`, `GET /documents/{id}`, `GET /documents`, `POST /documents/{id}/transition`
- Point d'entrée `python3 -m engine.http`
- 169 tests

### `ci-github-actions` (`ebd0de7`)

- Workflow GitHub Actions (`.github/workflows/tests.yml`)
- Déclenche sur `push` + `pull_request`, Python 3.12
- Nettoyage des logs HTTP dans les tests
- 46 tests

### `business-validation` (`2440384`)

- `engine/validation.py` : `DocumentValidator` (règles de création et de transition)
- Intégration dans `engine/api.py` (`create_document`, `transition_document`)
- 59 tests

### `api-authentication` (`d6510d5`)

- `engine/auth.py` : `TokenAuth` (`Bearer` token)
- `engine/http.py` : auth sur toutes les routes sauf `/health` (401 sinon)
- 70 tests

### `openapi-docs` (`6fddd95`)

- `docs/openapi.yaml` : OpenAPI 3.0.3 (5 endpoints, schemas, BearerAuth)
- `docs/technique/05-http-api.md` : guide de démarrage et exemples curl
- `tests/test_openapi_docs.py` (3 tests)
- 90 tests

### `docker-deployment` (`996e09f`)

- `Dockerfile` (base python:3.12-slim, EXPOSE 8080)
- `docker-compose.yml` (service `teamai-api`, port 8080, volume `./data:/app/data`)
- `.dockerignore` (.git, __pycache__, *.pyc, .venv, data)
- Test de configuration `tests/test_deployment_config.py`
- 90 tests
