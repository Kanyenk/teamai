# API StockTransfer (Stock Transfer)

## Endpoints

### POST /api/v1/wms/stock-transfers
Créer un(e) stock transfer.

**Corps de requête :**
```json
{
  "organisation_id": "org-1",
  "from_warehouse_id": "wh-1",
  "to_warehouse_id": "wh-2",
  "product_id": "prod-1",
  "quantity": 10,
  "status": "draft",
  "note": "Transfert urgent",
}
```

**Réponse (201) :** `{"item": {...}}`

### GET /api/v1/wms/stock-transfers
Lister par organisation. **Paramètre :** `organisation_id` (requis).

**Réponse (200) :** `{"items": [...]}`

### GET /api/v1/wms/stock-transfers/{id}
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
