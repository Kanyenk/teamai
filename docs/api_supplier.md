# API Supplier (Supplier)

## Endpoints

### POST /api/v1/wms/suppliers
Créer un(e) supplier.

**Corps de requête :**
```json
{
  "organisation_id": "org-1",
  "name": "Fournisseur Test",
  "email": "contact@fournisseur.fr",
  "phone": "+33123456789",
  "address": "12 rue du Commerce",
}
```

**Réponse (201) :** `{"item": {...}}`

### GET /api/v1/wms/suppliers
Lister par organisation. **Paramètre :** `organisation_id` (requis).

**Réponse (200) :** `{"items": [...]}`

### GET /api/v1/wms/suppliers/{id}
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
