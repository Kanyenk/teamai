# API — Moteur de documents XoHive (engine-api-v1)

Ce document décrit l'API HTTP exposée par le moteur de documents XoHive pour
la livraison lot engine-api-v1.

## Objectif de l'API

L'API expose les opérations minimales du moteur de documents XoHive :

- création d'un document comptable (FACT, BC, BL, NC, RS, CHQ) ;
- lecture, liste, ouverture, signature, envoi, annulation et deletion ;
- publication d'écritures sur le ledger ;
- création et lecture de transactions.

L'API est conçue pour être portable (FastAPI, Flask, Django, serveur HTTP
natif) ; la couche HTTP de base est un micro-framework mock autonome.

## Routes ou fonctions exposées

### Documents

| Méthode | Chemin | Corps | Description |
|---------|--------|-------|-------------|
| GET | `/api/v1/documents` | - | Liste les documents |
| POST | `/api/v1/documents` | `{doc_type, numero_serie, date_creation, org_id, ...}` | Crée un document |
| GET | `/api/v1/documents/{id}` | - | Récupère un document |
| PUT | `/api/v1/documents/{id}` | `{changes}` | Met à jour (schéma, pas la persistance) |
| DELETE | `/api/v1/documents/{id}` | - | Supprime un document (marque `supprime`) |

### Écritures et transactions

| Méthode | Chemin | Corps | Description |
|---------|--------|-------|-------------|
| POST | `/api/v1/ledger/post` | `{debit, credit, account}` | Poste une écriture |
| POST | `/api/v1/transactions/create` | `{doc_id, type, payload}` | Crée une transaction |
| GET | `/api/v1/transactions/{id}` | - | Récupère une transaction |

### États de document

| État | Description |
|------|-------------|
| brouillon | État initial |
| brouillon_pdf | PDF généré |
| envoye | Document envoyé |
| receive | Reçu |
| en_cours | En cours de traitement |
| execute | Exécuté |
| ecrit | Écrit |
| ferme | Fermé |
| annule | Annulé |
| supprime | Supprimé |

## Entrées / Sorties

### Exemple de création de document

**Entrée (POST /api/v1/documents)**
```json
{
  "doc_type": "FACT",
  "numero_serie": 1,
  "date_creation": "2026-11-02",
  "org_id": 1,
  "exposer": "Comptable",
  "currency": "EUR",
  "retention": 0.0,
  "balance": 0.0
}
```

**Sortie (201 Created)**
```json
{
  "document": {
    "id": 1,
    "doc_type": "FACT",
    "numero_serie": 1,
    "etat": "brouillon"
  }
}
```

### Exemple de liste

**Entrée (GET /api/v1/documents?limit=2&offset=0)**
```json
{
  "documents": [],
  "limit": 2
}
```

## Erreurs

| Code | Message | Statut |
|------|---------|--------|
| XOBHE422 | Unprocessable Entity | 422 |
| DOCUMENT_ERROR | Erreur de document | 400 |
| TRANSITION_ERROR | Transition refusée | 409 |
| BALANCE_ERROR | Équilibre invalide | 409 |
| VALIDATION_ERROR | Validation échouée | 400 |
| CONFIG_ERROR | Erreur de configuration | 500 |
| STORAGE_ERROR | Erreur de stockage | 500 |

## Limites V1

- Pas de persistance définitive : les documents sont gérés en mémoire ou
  relayés vers les couches inférieures du socle.
- Pas d'authentification ni de mai-sécurité (simplification V1).
- Les états de transition sont contrôlés, mais les écritures ne sont pas
  encore vérifiées sur le ledger.
- L'API est principalement un prototype de couche d'accès ; les
  implémentations Finales seront adaptées (FastAPI, GraphQL, etc.).
- Les routes `/api/v1/...` doivent rester stables pour les versions suivantes
  (v1.1, v2.0).
