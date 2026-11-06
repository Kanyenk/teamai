# API Returns (Retours clients)

## Endpoints

### POST /api/v1/wms/returns
Créer un retour client.

**Corps de requête :**
```json
{
  "organisation_id": "org-1",
  "order_id": "ord-1",
  "product_id": "prod-1",
  "quantity": 2,
  "reason": "Produit défectueux"
}
```

**Réponse (201) :**
```json
{
  "item": {
    "id": "ret-1",
    "organisation_id": "org-1",
    "order_id": "ord-1",
    "product_id": "prod-1",
    "quantity": 2,
    "reason": "Produit défectueux",
    "status": "draft",
    "refund_amount": 0.0,
    "created_at": "2026-11-06T18:00:00+00:00",
    "updated_at": "2026-11-06T18:00:00+00:00"
  }
}
```

### GET /api/v1/wms/returns
Lister les retours d'une organisation.

**Paramètre :** `organisation_id` (requis).

**Réponse (200) :**
```json
{
  "items": [
    {
      "id": "ret-1",
      "organisation_id": "org-1",
      "order_id": "ord-1",
      "product_id": "prod-1",
      "quantity": 2,
      "reason": "Produit défectueux",
      "status": "draft",
      "refund_amount": 0.0,
      "created_at": "2026-11-06T18:00:00+00:00",
      "updated_at": "2026-11-06T18:00:00+00:00"
    }
  ]
}
```

### GET /api/v1/wms/returns/{id}
Consulter un retour.

**Réponse (200) :** même structure que la création.

**Réponse (404) :** retour inexistant.

### POST /api/v1/wms/returns/{id}/request
Demander le retour (draft → requested).

**Réponse (200) :**
```json
{
  "item": {
    "id": "ret-1",
    "status": "requested"
  }
}
```

**Réponse (400) :** transition invalide.

### POST /api/v1/wms/returns/{id}/receive
Réceptionner le retour (requested → received).

**Réponse (200) :**
```json
{
  "item": {
    "id": "ret-1",
    "status": "received"
  }
}
```

**Réponse (400) :** transition invalide.

### POST /api/v1/wms/returns/{id}/refund
Rembourser le retour (received → refunded).

**Corps de requête :**
```json
{
  "amount": 50.0
}
```

**Réponse (200) :**
```json
{
  "item": {
    "id": "ret-1",
    "status": "refunded",
    "refund_amount": 50.0
  }
}
```

**Réponse (400) :** transition invalide ou montant négatif.

### POST /api/v1/wms/returns/{id}/cancel
Annuler le retour (draft/requested/received → cancelled).

**Réponse (200) :**
```json
{
  "item": {
    "id": "ret-1",
    "status": "cancelled"
  }
}
```

**Réponse (400) :** retour déjà refunded ou cancelled.

## Codes HTTP

| Code | Signification |
|---|---|
| 201 | Retour créé |
| 200 | Retour consulté, listé ou transition appliquée |
| 400 | Transition invalide ou champ manquant |
| 404 | Retour inexistant |

## Cycle de vie

```text
draft → requested → received → refunded
  ↓         ↓         ↓
  └─────────┴─────────┴──→ cancelled
```

## Authentification

Tous les endpoints nécessitent un header `Authorization: Bearer <token>`.
