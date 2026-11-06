# API Shipments (Expéditions)

## Endpoints

### POST /api/v1/wms/shipments
Créer une expédition client.

**Corps de requête :**
```json
{
  "organisation_id": "org-1",
  "order_id": "ord-1",
  "warehouse_id": "wh-1",
  "product_id": "prod-1",
  "quantity": 5
}
```

**Réponse (201) :**
```json
{
  "item": {
    "id": "shp-1",
    "organisation_id": "org-1",
    "order_id": "ord-1",
    "warehouse_id": "wh-1",
    "product_id": "prod-1",
    "quantity": 5,
    "status": "draft",
    "carrier": null,
    "tracking_number": null,
    "created_at": "2026-11-06T17:00:00+00:00",
    "updated_at": "2026-11-06T17:00:00+00:00"
  }
}
```

### GET /api/v1/wms/shipments
Lister les expéditions d'une organisation.

**Paramètre :** `organisation_id` (requis).

**Réponse (200) :**
```json
{
  "items": [
    {
      "id": "shp-1",
      "organisation_id": "org-1",
      "order_id": "ord-1",
      "warehouse_id": "wh-1",
      "product_id": "prod-1",
      "quantity": 5,
      "status": "draft",
      "carrier": null,
      "tracking_number": null,
      "created_at": "2026-11-06T17:00:00+00:00",
      "updated_at": "2026-11-06T17:00:00+00:00"
    }
  ]
}
```

### GET /api/v1/wms/shipments/{id}
Consulter une expédition.

**Réponse (200) :** même structure que la création.

**Réponse (404) :** expédition inexistante.

### POST /api/v1/wms/shipments/{id}/ship
Expédier une expédition (crée un mouvement `out` et passe à `shipped`).

**Corps de requête (optionnel) :**
```json
{
  "carrier": "UPS",
  "tracking_number": "TRK-123"
}
```

**Réponse (200) :**
```json
{
  "shipment": {
    "id": "shp-1",
    "status": "shipped",
    "carrier": "UPS",
    "tracking_number": "TRK-123"
  },
  "movement_id": "mov-1"
}
```

**Réponse (400) :** expédition déjà expédiée ou stock insuffisant.

## Codes HTTP

| Code | Signification |
|---|---|
| 201 | Expédition créée |
| 200 | Expédition consultée, listée ou expédiée |
| 400 | Expédition déjà expédiée ou stock insuffisant |
| 401 | Token manquant ou invalide |
| 404 | Expédition inexistante |

## Authentification

Tous les endpoints nécessitent un header `Authorization: Bearer <token>`.
