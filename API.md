# API.md — Documentation de l'API HTTP

## Liste des endpoints

| Méthode | Chemin | Auth requise | Corps attendu | Réponses possibles |
|---|---|---|---|---|
| GET | `/health` | Non | — | 200 |
| POST | `/documents` | Oui (Bearer) | JSON : `doc_type`, `numero_serie`, `org_id`, … | 201, 400, 401, 500 |
| GET | `/documents` | Oui (Bearer) | — | 200, 401, 500 |
| GET | `/documents/{id}` | Oui (Bearer) | — | 200, 401, 404, 500 |
| POST | `/documents/{id}/transition` | Oui (Bearer) | JSON : `etat`, `acteur` | 200, 400, 401, 404, 500 |

## Endpoint : GET /health

Sans authentification. Vérifie que le service tourne.

**Réponse 200**

```json
{"status": "ok"}
```

## Endpoint : POST /documents

Crée un document comptable.

**Auth :** `Authorization: Bearer <token>`

**Corps de la requête (JSON)**

```json
{
  "doc_type": "FACT",
  "numero_serie": 12345,
  "org_id": 1,
  "currency": "EUR",
  "retention": 0.0,
  "balance": 0.0
}
```

**Réponses**

| Code | Description |
|---|---|
| 201 | Document créé avec succès |
| 400 | Requête invalide (champs manquants, règles métier non respectées) |
| 401 | Token absent ou invalide |
| 500 | Erreur interne du serveur |

**Exemple curl**

```bash
curl -s -X POST http://localhost:8080/documents \
  -H "Authorization: Bearer tok_123" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_type": "FACT",
    "numero_serie": 12345,
    "org_id": 1,
    "currency": "EUR",
    "retention": 0.0,
    "balance": 0.0
  }'
```

**Réponse 201**

```json
{
  "status": "ok",
  "data": {
    "id": "doc-1a2b3c4d5e6f",
    "doc_type": "FACT",
    "numero_serie": 12345,
    "org_id": 1,
    "currency": "EUR",
    "retention": 0.0,
    "balance": 0.0,
    "date_creation": "2026-11-03T00:00:00Z",
    "etat": "brouillon"
  }
}
```

## Endpoint : GET /documents

Lister les documents (pagination).

**Auth :** `Authorization: Bearer <token>`

**Paramètres de requête**

| Paramètre | Type | Opt.| Description |
|---|---|---|---|
| `limit` | integer | Non | Nombre max de documents (1-100, par défaut 50) |
| `offset` | integer | Non | Décalage pour la pagination (par défaut 0) |

**Réponse 200**

```json
{
  "status": "ok",
  "data": {
    "items": [
      {
        "id": "doc-1a2b3c4d5e6f",
        "doc_type": "FACT",
        "numero_serie": 12345,
        "org_id": 1,
        "etat": "brouillon"
      }
    ],
    "total": 1,
    "limit": 50,
    "offset": 0
  }
}
```

**Exemple curl**

```bash
curl -s -X GET "http://localhost:8080/documents?limit=10&offset=0" \
  -H "Authorization: Bearer tok_123"
```

## Endpoint : GET /documents/{id}

Lire un document.

**Auth :** `Authorization: Bearer <token>`

**Paramètres de chemin**

| Paramètre | Type | Description |
|---|---|---|
| `id` | string | Identifiant du document |

**Réponses**

| Code | Description |
|---|---|
| 200 | Document trouvé |
| 401 | Token absent ou invalide |
| 404 | Document non trouvé |
| 500 | Erreur interne du serveur |

**Exemple curl**

```bash
curl -s -X GET http://localhost:8080/documents/doc-1a2b3c4d5e6f \
  -H "Authorization: Bearer tok_123"
```

**Réponse 200**

```json
{
  "status": "ok",
  "data": {
    "id": "doc-1a2b3c4d5e6f",
    "doc_type": "FACT",
    "numero_serie": 12345,
    "org_id": 1,
    "currency": "EUR",
    "retention": 0.0,
    "balance": 0.0,
    "date_creation": "2026-11-03T00:00:00Z",
    "etat": "brouillon"
  }
}
```

## Endpoint : POST /documents/{id}/transition

Appliquer une transition d'état.

**Auth :** `Authorization: Bearer <token>`

**Corps de la requête (JSON)**

```json
{
  "etat": "brouillon_pdf",
  "acteur": "system"
}
```

**Réponses**

| Code | Description |
|---|---|
| 200 | Transition appliquée avec succès |
| 400 | Transition refusée (règles métier non respectées) |
| 401 | Token absent ou invalide |
| 404 | Document non trouvé |
| 500 | Erreur interne du serveur |

**Exemple curl**

```bash
curl -s -X POST http://localhost:8080/documents/doc-1a2b3c4d5e6f/transition \
  -H "Authorization: Bearer tok_123" \
  -H "Content-Type: application/json" \
  -d '{"etat": "brouillon_pdf"}'
```

**Réponse 200**

```json
{
  "status": "ok",
  "data": {
    "id": "doc-1a2b3c4d5e6f",
    "doc_type": "FACT",
    "numero_serie": 12345,
    "org_id": 1,
    "currency": "EUR",
    "retention": 0.0,
    "balance": 0.0,
    "date_creation": "2026-11-03T00:00:00Z",
    "etat": "brouillon_pdf"
  }
}
```

## Format du token Bearer

Le token est transmis dans l'en-tête `Authorization` au format :

```
Authorization: Bearer <token>
```

### Exemples

```bash
# Avec un token supposé "tok_123"
curl -s -H "Authorization: Bearer tok_123" http://localhost:8080/health
```

### Règles de validation (TokenAuth.authenticate)

| Condition | Résultat |
|---|---|
| En-tête absent | `401` |
| Format incorrect (ex: `Bearer` seul) | `401` |
| Token invalide | `401` |
| Token valide | Autorisé |

### Variables d'environnement

| Variable | Description | Exemple |
|---|---|---|
|| `TEAMAI_TOKENS` | Liste des tokens valides (séparés par `,`) | `tok_123,dev-token` |
|| `TEAMAI_DB_PATH` | Chemin vers la base SQLite | `/app/data/teamai.db` |

---

## 8. Module CRM — Endpoints CRM

Documentation des routes REST pour le module CRM minimal.

### Companies

#### Lister les entreprises

**GET** `/api/v1/crm/companies`

**Réponse 200** : Liste des entreprises

#### Créer une entreprise

**POST** `/api/v1/crm/companies`

**Corps de la requête (JSON)**
```json
{
  "name": "Acme SARL",
  "siret": "12345678901234",
  "city": "Paris",
  "zip_code": "75001",
  "country": "FR",
  "website": "https://acme.com",
  "contact_person": "Jean Dupont",
  "email": "contact@acme.com",
  "organisation_id": "default-org"
}
```

**Réponses** :
| Code | Description |
|------|-------------|
| 201 | Entreprise créée avec succès |
| 400 | Requête invalide |
| 401 | Token absent ou invalide |
| 500 | Erreur interne |

---

#### Récupérer une entreprise

**GET** `/api/v1/crm/companies/{id}`

---

### Contacts

#### Lister les contacts

**GET** `/api/v1/crm/contacts`

---

#### Créer un contact

**POST** `/api/v1/crm/contacts`

**Corps de la requête (JSON)**
```json
{
  "organisation_id": "default-org",
  "company_id": "crm-756253312ee0",
  "first_name": "Jean",
  "last_name": "Dupont",
  "email": "jean@acme.com",
  "phone": "+33612345678",
  "is_active": true
}
```

---

#### Récupérer un contact

**GET** `/api/v1/crm/contacts/{id}`

---

### Opportunities

#### Lister les opportunités

**GET** `/api/v1/crm/opportunities`

---

#### Créer une opportunité

**POST** `/api/v1/crm/opportunities`

**Corps de la requête (JSON)**
```json
{
  "organisation_id": "default-org",
  "company_id": "crm-756253312ee0",
  "title": "Demande de devis - Acme",
  "amount": 15000.00,
  "stage": "prospecting",
  "probability": 30.0,
  "close_date": "2026-12-31",
  "is_active": true
}
```

---

#### Récupérer une opportunité

**GET** `/api/v1/crm/opportunities/{id}`

---

### Pipeline

#### Récupérer le pipeline

**GET** `/api/v1/crm/pipeline/{company_id}`

---

### Activities

#### Lister les activités

**GET** `/api/v1/crm/activities`

---

#### Créer une activité

**POST** `/api/v1/crm/activities`

**Corps de la requête (JSON)**
```json
{
  "organisation_id": "default-org",
  "company_id": "crm-756253312ee0",
  "contact_id": "crm-8111e1c64bfd",
  "type": "appel",
  "subject": "Appel prospectif",
  "description": "Appel initial pour qualifier le prospect",
  "date": "2026-10-01T09:00:00Z",
  "status": "done",
  "is_active": true
}
```

---

## Codes d'erreur

|| Code | Description |
|---|---|---|
| 400 | Bad Request - Requête invalide |
| 401 | Unauthorized - Token manquant ou invalide |
| 404 | Not Found - Ressource introuvable |
| 500 | Internal Server Error |

---

## Exemples de requêtes

### Créer une entreprise

```bash
curl -X POST http://localhost:8081/api/v1/crm/companies \
  -H "Authorization: Bearer tok_123" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme SARL",
    "siret": "12345678901234",
    "city": "Paris",
    "zip_code": "75001",
    "country": "FR",
    "website": "https://acme.com",
    "contact_person": "Jean Dupont",
    "email": "contact@acme.com",
    "organisation_id": "default-org"
  }'
```

### Lister les opportunités

```bash
curl -X GET http://localhost:8081/api/v1/crm/opportunities \
  -H "Authorization: Bearer tok_123"
```

### Créer une activité

```bash
curl -X POST http://localhost:8081/api/v1/crm/activities \
  -H "Authorization: Bearer tok_123" \
  -H "Content-Type: application/json" \
  -d '{
    "organisation_id": "default-org",
    "company_id": "crm-756253312ee0",
    "contact_id": "crm-8111e1c64bfd",
    "type": "appel",
    "subject": "Appel prospectif",
    "description": "Appel initial pour qualifier le prospect",
    "date": "2026-10-01T09:00:00Z",
    "status": "done"
  }'
```

---
