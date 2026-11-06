# API Purchase Orders (Réceptions fournisseurs)

## Endpoints

### POST /api/v1/wms/purchase-orders
Créer une commande fournisseur.

**Corps de requête :**
```json
{
  "organisation_id": "org-1",
  "supplier_name": "Fournisseur A",
  "warehouse_id": "wh-1"
}
```

**Réponse (201) :**
```json
{
  "item": {
    "id": "po-1",
    "organisation_id": "org-1",
    "supplier_name": "Fournisseur A",
    "warehouse_id": "wh-1",
    "status": "draft",
    "reference": "PO-XXXXXXXX",
    "created_at": "2026-11-06T17:00:00+00:00",
    "updated_at": "2026-11-06T17:00:00+00:00"
  }
}
```

### GET /api/v1/wms/purchase-orders
Lister les commandes d'une organisation.

**Paramètre :** `organisation_id` (requis).

**Réponse (200) :**
```json
{
  "items": [
    {
      "id": "po-1",
      "organisation_id": "org-1",
      "supplier_name": "Fournisseur A",
      "warehouse_id": "wh-1",
      "status": "draft",
      "reference": "PO-XXXXXXXX",
      "created_at": "2026-11-06T17:00:00+00:00",
      "updated_at": "2026-11-06T17:00:00+00:00"
    }
  ]
}
```

### GET /api/v1/wms/purchase-orders/{id}
Consulter une commande.

**Réponse (200) :** même structure que la création.

**Réponse (404) :** commande inexistante.

### POST /api/v1/wms/purchase-orders/{id}/receive
Réceptionner une commande (passe le statut à `received`).

**Corps de requête :** aucun champ requis.

**Réponse (200) :**
```json
{
  "item": {
    "id": "po-1",
    "organisation_id": "org-1",
    "supplier_name": "Fournisseur A",
    "warehouse_id": "wh-1",
    "status": "received",
    "reference": "PO-XXXXXXXX",
    "created_at": "2026-11-06T17:00:00+00:00",
    "updated_at": "2026-11-06T17:01:00+00:00"
  }
}
```

**Réponse (400) :** commande déjà reçue ou annulée.

## Codes HTTP

| Code | Signification |
|---|---|
| 201 | Commande créée |
| 200 | Commande consultée, listée ou reçue |
| 400 | Transition invalide (déjà reçue/annulée) |
| 401 | Token manquant ou invalide |
| 404 | Commande inexistante |

## Authentification

Tous les endpoints nécessitent un header `Authorization: Bearer <token>`.
