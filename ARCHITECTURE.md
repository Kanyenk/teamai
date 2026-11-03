# ARCHITECTURE — TeamAI Engine

## Schéma des modules

```
┌─────────────────┐
│  engine/        │
│  ┌───────────┐  │
│  │ __init__.py │  │  État valides, TRANSITIONS, Document, DocumentError, compute_state_hash
│  ├───────────┤  │
│  │ api.py    │  │  API minimale (XoHiveError, create_document, transition_document)
│  │ auth.py   │  │  TokenAuth — vérifie le header Bearer
│  │ repository.py │  │  DocumentRepository — SQLite (save, get, list)
│  │ documents.py │  │  Document, DocumentStore, DocumentQuery, DocumentEditor
│  │ http.py   │  │  HttpHandler (BaseHTTPRequestHandler), make_app, main
│  │ exceptions.py │  │  EngineError, DocumentError, TransitionError…
│  │ ledger.py   │  │  Ledger — moteur d'écriture comptable
│  │ transactions.py │  │  TransactionStore — stockage événementiel
│  │ validation.py │  │  DocumentValidator — règles business
│  └───────────┘  │
└─────────────────┘
        │
        ▼
┌─────────────────┐
│  tests/         │
│  test_*.py      │
│  (90 tests)     │
└─────────────────┘
        │
        ▼
┌─────────────────┐
│  docker-compose │
│  Dockerfile     │
│  .dockerignore  │
└─────────────────┘
```

## Flux d'une requête HTTP de bout en bout

```
Client → HTTP(S)
  │
  ▼
HttpHandler._handle_one_request()
  │
  ├─ /health  →  sans authentification, retourne {"status": "ok"} (200)
  │
  ├─ /documents (POST)
  │   ├─ parse JSON du body
  │   ├─Validator validate_creation (doc_type, numero_serie, org_id, currency, retention, balance)
  │   ├─ DocumentRepository.save(document)
  │   └─ retourne 201 avec le document créé
  │
  ├─ /documents (GET)  →  liste paginée (limit=50, offset=0)
  │
  ├─ /documents/{id} (GET)
  │   ├─ DocumentRepository.get(id)
  │   ├─ si None → 404
  │   └─ retourne le document (200)
  │
  └─ /documents/{id}/transition (POST)
      ├─ parse JSON {"etat": "...", "acteur": "..."}
      ├─ DocumentRepository.get(id)
      ├─ if None → 404
      ├─ DocumentValidator.validate_transition(document, etat)
      ├─ document.transition(etat, acteur)
      └─ retourne 200 avec le document
```

## Modèle de données Document

### Champs d'un document

| Champ | Type | Description | Exemple |
|---|---|---|---|
| `id` | str | Identifiant unique | `"doc-1a2b3c4d5e6f"` |
| `doc_type` | str | Type de document (FACT, BC, BL, NC, RS, CHQ) | `"FACT"` |
| `numero_serie` | int | Numéro de série | `12345` |
| `org_id` | int | Identifiant de l'organisation | `1` |
| `date_creation` | str (ISO 8601) | Date de création | `"2026-11-03T00:00:00Z"` |
| `etat` | str | État courant | `"brouillon"` |
| `currency` | str | Devise | `"EUR"` |
| `retention` | float | Taux de rétention | `0.0` |
| `balance` | float | Solde | `0.0` |
| `etat_hash` | str | Haché SHA-256 de l'état | `"a1b2c3…"` |

### États (machine à états)

```python
STATE_DRAFT = "brouillon"
STATE_DRAFT_PDF = "brouillon_pdf"
STATE_SENT = "envoye"
STATE_RECEIVED = "receive"
STATE_IN_PROGRESS = "en_cours"
STATE_EXECUTED = "execute"
STATE_WRITTEN = "ecrit"
STATE_CLOSED = "ferme"
STATE_CANCELLED = "annule"
STATE_DELETED = "supprime"
```

### Transitions autorisées

```python
TRANSITIONS = {
    "brouillon": ["brouillon_pdf"],
    "brouillon_pdf": ["envoye"],
    "envoye": ["receive"],
    "receive": ["en_cours"],
    "en_cours": ["execute"],
    "execute": ["ecrit"],
    "ecrit": ["ferme", "annule"],
    "annule": ["ecrit"],
    "ferme": [],
    "supprime": [],
}
```

### Règles de validation

| Règle | Valeurs acceptées |
|---|---|
| `doc_type` | FACT, BC, BL, NC, RS, CHQ (strictement) |
| `numero_serie` | entier strictement positif |
| `org_id` | entier strictement positif |
| `currency` | chaîne de 3 caractères (ex: EUR, USD) |
| `retention` | nombre entre 0 et 1 |
| `balance` | nombre, ≥ 0 |

## Rôle de chaque classe principale

| Classe | Rôle |
|---|---|
| `engine.__init__.Document` | Représentation d'un document comptable avec machine à états |
| `engine.__init__.DocumentError` | Erreur de validation / de manipulation d'un document |
| `engine.__init__.compute_state_hash` | Hachage SHA-256 immuable de l'état du document |
| `engine.auth.TokenAuth` | Vérifie `Authorization: Bearer <token>` |
| `engine.repository.DocumentRepository` | Couche SQLite : save / get / list / close |
| `engine.documents.DocumentStore` | Stockage événementiel (immuable) |
| `engine.documents.DocumentEditor` | Éditeur de documents avec validation de transitions |
| `engine.http.HttpHandler` | Gère les requêtes HTTP (routes, JSON, états) |
| `engine.http.make_app` | Ecoute le `store` et `auth` sur la classe du handler |
| `engine.validation.DocumentValidator` | Règles business : validation de création et de transition |
| `engine.api.XoHiveError` | Erreur générique de l'API avec code HTTP |
