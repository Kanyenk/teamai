# API Stock Counts (Inventaires)

## Endpoints

### POST /api/v1/wms/stock-counts
Créer un comptage d'inventaire.

**Corps de requête :**
```json
{
  "organisation_id": "org-1",
  "warehouse_id": "wh-1",
  "product_id": "prod-1",
  "counted_quantity": 5
}
```

**Réponse (201) :**
```json
{
  "item": {
    "id": "count-1",
    "organisation_id": "org-1",
    "warehouse_id": "wh-1",
    "product_id": "prod-1",
    "counted_quantity": 5,
    "status": "draft"
  }
}
```

### GET /api/v1/wms/stock-counts/{id}
Consulter un comptage.

**Réponse (200) :**
```json
{
  "item": {
    "id": "count-1",
    "organisation_id": "org-1",
    "warehouse_id": "wh-1",
    "product_id": "prod-1",
    "counted_quantity": 5,
    "status": "draft"
  }
}
```

**Réponse (404) :** comptage inexistant.

### POST /api/v1/wms/stock-counts/{id}/adjust
Ajuster un comptage (crée un mouvement de régularisation).

**Corps de requête (optionnel) :**
```json
{
  "reason": "inventaire annuel"
}
```

**Réponse (200) :**
```json
{
  "count_id": "count-1",
  "theoretical_quantity": 5,
  "counted_quantity": 3,
  "difference": -2,
  "movement_id": "mov-1",
  "status": "adjusted"
}
```

Si l'écart est nul, `movement_id` est `null` et aucun mouvement n'est créé.

**Réponse (400) :** comptage déjà ajusté.

## Codes HTTP

| Code | Signification |
|---|---|
| 201 | Comptage créé |
| 200 | Comptage consulté ou ajusté |
| 400 | Comptage déjà ajusté |
| 401 | Token manquant ou invalide |
| 404 | Comptage inexistant |

## Authentification

Tous les endpoints nécessitent un header `Authorization: Bearer <token>`.
