# API Barcode (Barcode)

## Endpoints

### POST /api/v1/wms/barcodes
Créer un(e) barcode.

**Corps de requête :**
```json
{
  "organisation_id": 'org-1',
  "product_id": 'prod-1',
  "code": '3012345678900',
  "type": 'ean13',
  "label": 'Code-barres produit A',
}
```

**Réponse (201) :** `{"item": {...}}`

### GET /api/v1/wms/barcodes
Lister par organisation. **Paramètre :** `organisation_id` (requis).

**Réponse (200) :** `{"items": [...]}`

### GET /api/v1/wms/barcodes/{id}
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
