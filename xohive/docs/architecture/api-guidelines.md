# API Guidelines — XoHive

> Règles et conventions pour l'API REST du projet XoHive.
>
> Elles s'appliquent à toutes les endpoints exposées par les modules futurs (CRM, Ventes, Achats, etc.).

---

## 1. Conception

### 1.1 Principes d'architecture

- **Aucuneécriture directe** : toute requête HTTP passe par un endpoint ; les modules s'expriment par des services et des repositories.
- **Sécurité par défaut** : tout endpoint non spécifié est privé. Il faut une règle d'API claire.
- **Authentification par token** : le header `Authorization: Bearer <token>` est requis sur tous les endpoints sauf `/health` et `/auth/login`.
- **Pagination** : les endpoints de liste acceptent `limit` et `offset` `GET /api/v1/documents?limit=50&offset=0`.
- **Transactions** : les écritures doivent être atomices. Les repository SQLite utilisent des transactions explicites.

### 1.2 Bonnes pratiques

- Tous les endpoints renvoient une réponse JSON structurée.
- Les erreurs sont renvoyées avec le schéma `{error: {code, message, details}}`.
- Les timestamps sont au format ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`).
- L'URL ne contient pas de query string pour les filtres complexes : utiliser les paramètres de chemin pour les identifiants.

### 1.3 Sécurité

| Mécanisme | Utilisation |
|---|---|
| `Authorization: Bearer <token>` | Auth sur tous les endpoints |
| CORS | À configurer côté serveur |
| Rate limiting | À configurer côté proxy (nginx, traefik) |
| Hardening | Rejection des droits super-users, get-only sur le token |

### 1.4 Versioning

- La version de l'API est dans l'URL : `/api/v1/...`
- Les changements majeurs nécessitent une nouvelle version (`v2`, `v3`).

---

## 2. Conventions de nommage

| Élément | Règle | Exemple |
|---|---|---|
| Ressource | Pluriel, kebab-case | `/api/v1/organizations` |
| ID | `id` | `/api/v1/organizations/{id}` |
| Paramètres de pagination | `limit`, `offset` | `?limit=10&offset=20` |
| Filtres | `filter_<champ>` | `?filter_status=draft` |
| Tri | `sort=<champ>` | `?sort=-created_at` |
| Champs JSON | snake_case | `{"first_name": "Jean"}` |

### Exemples d'URLs

```
GET    /api/v1/health
POST   /api/v1/auth/login
GET    /api/v1/organizations
GET    /api/v1/organizations/{id}
POST   /api/v1/organizations/{id}/documents
GET    /api/v1/documents/{doc_id}/transitions
```

---

## 3. Schéma de réponse

### 3.1 Succès

```json
{
  "data": { ... }
}
```

### 3.2 Pagination

```json
{
  "data": [ ... ],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 100
  }
}
```

### 3.3 Erreur

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "doc_type invalide",
    "details": {
      "field": "doc_type",
      "value": "XYZ",
      "allowed": ["FACT", "BC", "BL", "NC", "RS", "CHQ"]
    }
  }
}
```

---

## 4. Codes HTTP

| Code | Utilisation |
|---|---|
| 200 | Succès (GET, PUT, PATCH) |
| 201 | Création (POST) |
| 204 | Suppression (DELETE) |
| 400 | Bad Request (champs invalides) |
| 401 | Unauthorized (token manquant ou invalide) |
| 403 | Forbidden (pas de permission) |
| 404 | Not Found (ressource introuvable) |
| 409 | Conflict (resemblant à une contrainte) |
| 422 | Unprocessable Entity (ingestion échouée) |
| 429 | Too Many Requests (rate limiting) |
| 500 | Internal Server Error |

---

## 5. Authentification

### 5.1 Login

`POST /api/v1/auth/login`

Requête :
```json
{
  "email": "alice@acme.com",
  "password": "secret123"
}
```

Réponse succès :
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "user-1a2b3c",
    "email": "alice@acme.com",
    "first_name": "Alice",
    "last_name": "Martin",
    "organisation_id": "org-1a2b3c"
  }
}
```

### 5.2 Propager

Tout appel ultérieur doit inclure le header :
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

Si le token est invalide ou expiré, la réponse est `401 Unauthorized` avec le schéma d'erreur.

---

## 6. Exemples d'endpoints

| Méthode | URL | Description | Auth |
|---|---|---|---|
| `GET` | `/api/v1/health` | Santé du service | Non |
| `POST` | `/api/v1/auth/login` | Obtenir un token | Non |
| `GET` | `/api/v1/organizations` | Lister les organisations | Oui |
| `POST` | `/api/v1/organizations` | Créer une organisation | Oui |
| `GET` | `/api/v1/organizations/{id}` | Lire une organisation | Oui |
| `PUT` | `/api/v1/organizations/{id}` | Mettre à jour | Oui |
| `DELETE` | `/api/v1/organizations/{id}` | Supprimer | Oui |
| `GET` | `/api/v1/users` | Lister les utilisateurs | Oui |
| `POST` | `/api/v1/users` | Créer un utilisateur | Oui |
| `GET` | `/api/v1/roles` | Lister les rôles | Oui |
| `GET` | `/api/v1/documents` | Lister les documents | Oui |
| `POST` | `/api/v1/documents` | Créer un document | Oui |
| `GET` | `/api/v1/documents/{id}` | Lire un document | Oui |
| `POST` | `/api/v1/documents/{id}/transitions` | Appliquer une transition | Oui |
| `GET` | `/api/v1/audit` | Audit trail | Oui |
| `GET` | `/api/v1/ledger` | État du livre de compte | Oui |

---

## 7. Règles de validation

### 7.1 Validation des champs

| Champ | Règle |
|---|---|
| `email` | Format email valide, unique dans l'organisation |
| `password` | ≥ 12 caractères, must contenu 1 chiffre, 1 majuscule, 1 minuscule |
| `doc_type` | Must être `FACT`, `BC`, `BL`, `NC`, `RS`, ou `CHQ` |
| `numero_serie` | Entier > 0 |
| `currency` | Code ISO 3 (ex: `EUR`) |
| `balance` | Nombre ≥ 0 |
| `retention` | Nombre entre 0 et 1 |

### 7.2 Règles métier

- Un `User` appartient à une seule `Organization`.
- Un `Role` appartient à une seule `Organization`.
- Un `Document` appartient à une seule `Organization`.
- Les permissions sont vérifiées via `has_permission(user, permission_code)`.

---

## 8. Événements (Event Bus)

Toutes les mutations de l'API déclenchent des événements :
- `organization.created`
- `organization.updated`
- `user.created`
- `user.updated`
- `role.updated`
- `document.created`
- `document.updated`
- `document.transitioned`
- `audit.created`
- `ledger.written`

Le `EventBus` route les événements vers les handlers `sync` et `async`.

---

*Document généré le 2026-11-03. Propriété : XoHive.*
