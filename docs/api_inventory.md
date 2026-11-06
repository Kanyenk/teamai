# API Inventory (Inventory)

## Endpoints

### POST /api/v1/wms/inventories
Créer un(e) inventory.

**Corps de requête :**
```json
{
  "organisation_id": "org-1",
  "warehouse_id": "wh-1",
  "product_id": "prod-1",
  "counted_quantity": 5,
  "expected_quantity": 4,
  "note": "Inventaire annuel",
}
```

**Réponse (201) :** `{"item": {...}}`

### GET /api/v1/wms/inventories
Lister par organisation. **Paramètre :** `organisation_id` (requis).

**Réponse (200) :** `{"items": [...]}`

### GET /api/v1/wms/inventories/{id}
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
