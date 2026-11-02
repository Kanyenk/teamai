```markdown
# API — moteur de documents (engine-api-v1)

Ce document décrit l'API exposée par le moteur de documents (socle V0)
dans le lot `engine-api-v1`.

## But du lot

- Exposer une API minimale du moteur de documents.
- Définir les routes, les schémas d'entrée/sortie et les erreurs.
- Ajouter des tests exécutables.
- Ne pas implémenter de persistance définitive sans validation.

## Positionnement

Le lot de base (`engine-api-v1`) s'articule autour de `engine/api.py` :

| Fichier | Rôle |
|---------|------|
| `engine/api.py` | Couche d'accès HTTP d'un serveur minimal, sans framework externe. |
| `engine/exceptions.py` | Exceptions métier réutilisées par l'API. |
| `engine/state_machine.py` | États/valeurs du document, pour la validation des routes. |
| `engine/transactions.py` | Transaction métier (gardée séparée). |
| `engine/documents.py` | `DocumentStore` — en mémoire, à remplacer par la persistance. |

## Routes

###Documentation)

Les routes sont définies dans `engine/api.py` sous forme de dictionnaire `ROUTES` ;

| Méthode | Route | Description | Input schema | Output schema |
|---------|-------|-------------|--------------|---------------|
| `GET` | `/api/v0/documents` | Lister les documents | `limit`, `offset` (query) | `{"documents": [...], "limit": n}` |
| `GET` | `/api/v0/documents/{doc_id}` | Obtenir un document | `id` (query) | `{"document": {...}}` ou `404` |
| `POST` | `/api/v0/documents` | Créer un document | `doc_type`, `numero_serie`, `date_creation`, `org_id`, etc. | `201`, `{"document": {...}}` |
| `POST` | `/api/v0/documents/{doc_id}/open` | Ouvrir un document | `actor` | `200`, `{"etat": "edite"}` |
| `POST` | `/api/v0/documents/{doc_id}/resign` | Générer le PDF | `actor` | `200`, `{"etat": "brouillon_pdf"}` |
| `POST` | `/api/v0/documents/{doc_id}/send` | Envoyer le document | `actor` | `200`, `{"etat": "envoye"}` |
| `POST` | `/api/v0/documents/{doc_id}/cancel` | Annuler | `actor` | `200`, `{"etat": "annule"}` |
| `POST` | `/api/v0/documents/{doc_id}/delete` | Supprimer | `actor` | `200`, `{"etat": "supprime"}` |
| `POST` | `/api/v0/ledger/post` | Post d'écriture | `libelle`, `entries` | `200`, `{"written": n, "balance": "0.00"}` |
| `POST` | `/api/v0/transactions/create` | Créer une transaction | `type_`, `payload`, `actor` | `201`, `{"tx_id": ..., "status": "created"}` |
| `GET` | `/api/v0/transactions/{tx_id}` | Obtenir une transaction | `tx_id` | `200`, `{"tx": {...}}` |

## Schémas d'entrée/sortie

### Création d'un document (POST /api/v0/documents)

Entrée (JSON) :

```json
{
  "doc_type": "FACT|BC|BL|NC|RS|CHQ",
  "numero_serie": 1,
  "date_creation": "2026-11-02",
  "org_id": 1,
  "exposer": "Comptable",
  "currency": "EUR",
  "retention": 0.0,
  "balance": 0.0
}
```

Sortie (JSON) :

```json
{
  "document": {
    "id": null,
    "doc_type": "FACT",
    "numero_serie": 1,
    "date_creation": "2026-11-02",
    "org_id": 1,
    "exposer": "Comptable",
    "currency": "EUR",
    "retention": 0.0,
    "balance": 0.0,
    "etat": "brouillon",
    "hash_etat": "...",
    "created_by": "system",
    "updated_by": "system",
    "etats": [...]
  }
}
```

### Post d'écriture (POST /api/v0/ledger/post)

Entrée (JSON) :

```json
{
  "libelle": "Achat fournisseur",
  "entries": [
    {"compte_id": 1110, "debit": 100.0, "credit": 0.0},
    {"compte_id": 4110, "debit": 0.0, "credit": 100.0}
  ],
  "created_by": "system"
}
```

Sortie (JSON) :

```json
{
  "written": 2,
  "balance": "0.00"
}
```

### Erreurs HTTP

| Code | Nom | Définition |
|------|-----|------------|
| 400 | BadRequest | Donnée invalide (champs manquants, format, etc.) |
| 401 | Unauthorized | Non authentifié |
| 403 | Forbidden | Accès refusé |
| 404 | NotFound | Ressource introuvable |
| 409 | Conflict | Conflit d'état (ex: passer un document déjà final) |
| 422 | UnprocessableEntity | Erreur métier (ex: solde non équilibré) |
| 500 | InternalServerError | Erreur technique inattendue |

Les erreurs sont formatées comme suit :

```json
{
  "error": {
    "code": "DOC001",
    "message": "message générique, sans détails sensibles"
  }
}
```

## Tests exécutables

### Lancer les tests

```bash
cd /opt/data/home/projects/teamai
python3 -m pytest tests/test_engine_api.py -v
```

### Structure

```
tests/
├── test_engine_api.py      # Tests de l'API
└── conftest.py             # Fixtures partagées
```

### Exemple de test

```python
def test_create_document():
    from engine.api import XoHiveError, Document
    from engine.state_machine import compute_state_hash

    doc = Document(
        doc_type="FACT",
        numero_serie=1,
        date_creation="2026-11-02",
        org_id=1,
        exposer="Comptable",
        currency="EUR",
        retention=0.0,
        balance=0.0,
    )

    assert doc.etat == "brouillon"
    assert doc.est_final() is False
    assert doc.etat_hash == compute_state_hash(
        "brouillon", 1, 1, "EUR", 0.0, 0.0
    )
```

## État de l'implémentation

- Couche d'accès HTTP : implémentée (micro-framework mock, sans dépendance externe).
- Persistance : **non implémentée** — à valider avant tout déploiement.
- Machines à états : implémentées dans `engine/state_machine.py`.
- Transactions : implémentées dans `engine/transactions.py`.
