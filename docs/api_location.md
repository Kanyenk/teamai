# API Location (Location)

## Endpoints

### POST /api/v1/wms/locations
Créer un(e) location.

**Corps de requête :**
```json
{
  "organisation_id": 'org-1',
  "warehouse_id": 'wh-1',
  "code": 'A-01-03',
  "name": 'Allée A, rayon 01, niveau 03',
  "zone": 'picking',
  "capacity": 100,
}
```

**Réponse (201) :** `{"item": {...}}`

### GET /api/v1/wms/locations
Lister par organisation. **Paramètre :** `organisation_id` (requis).

**Réponse (200) :** `{"items": [...]}`

### GET /api/v1/wms/locations/{id}
Consulter. **Réponse (200/404).**

## Codes HTTP

| Code | Signification |
|---|---|
| 201 | Créé |
| 200 | Consulté/listé |
| 400 | Champ manquant/invalide |
| 404 | Introuvable |

## Authentification

Header `Authorization: Bearer <token>`.
