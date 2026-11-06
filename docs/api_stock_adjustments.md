# API Stock Adjustments (Ajustements de stock)

## Endpoints

### POST /api/v1/wms/stock-adjustments
Créer un ajustement de stock.

**Corps de requête :**
```json
{
  "organisation_id": "org-1",
  "warehouse_id": "wh-1",
  "product_id": "prod-1",
  "quantity": 5,
  "reason": "correction",
  "note": "Inventaire annuel"
}
```

**Réponse (201) :**
```json
{
  "item": {
    "id": "adj-1",
    "organisation_id": "org-1",
    "warehouse_id": "wh-1",
    "product_id": "prod-1",
    "quantity": 5,
    "reason": "correction",
    "note": "Inventaire annuel",
    "created_at": "2026-11-06T18:00:00+00:00",
    "updated_at": "2026-11-06T18:00:00+00:00"
  }
}
```

### GET /api/v1/wms/stock-adjustments
Lister les ajustements d'une organisation.

**Paramètre :** `organisation_id` (requis).

**Réponse (200) :**
```json
{
  "items": [
    {
      "id": "adj-1",
      "organisation_id": "org-1",
      "warehouse_id": "wh-1",
      "product_id": "prod-1",
      "quantity": 5,
      "reason": "correction",
      "note": "Inventaire annuel",
      "created_at": "2026-11-06T18:00:00+00:00",
      "updated_at": "2026-11-06T18:00:00+00:00"
    }
  ]
}
```

### GET /api/v1/wms/stock-adjustments/{id}
Consulter un ajustement.

**Réponse (200) :** même structure que la création.

**Réponse (404) :** ajustement inexistant.

## Codes HTTP

| Code | Signification |
|---|---|
| 201 | Ajustement créé |
| 200 | Ajustement consulté ou listé |
| 400 | Champ manquant ou raison invalide |
| 404 | Ajustement inexistant |

## Raisons valides

| Raison | Signification |
|---|---|
| damage | Produit endommagé |
| loss | Perte de stock |
| found | Stock trouvé (surplus) |
| correction | Correction d'inventaire |
| other | Autre raison |

## Quantité

- **Positif** : entrée de stock (surplus, correction à la hausse).
- **Négatif** : sortie de stock (perte, casse, correction à la baisse).
- **Zéro** : interdit.

## Authentification

Tous les endpoints nécessitent un header `Authorization: Bearer <token>`.
