# Guide de l'API HTTP — Version OpenApi

Ce document décrit l'API HTTP minimale du moteur de documents TeamAI. Elle permet
de créer, lire et transformer des documents comptables. L'API est exposée via
`http.server` (stdlib Python), sans framework externe.

---

## 1. Démarrer le service

### 1.1 Prérequis

- Python 3.12+ (disponible sur le conteneur Hermes)
- Modules standard uniquement (`http.server`, `sqlite3`, `json`, etc.)

### 1.2 Créer la base de données

```bash
python3 -c "from engine.repository import DocumentRepository; DocumentRepository('documents.db')"
```

### 1.3 Démarrer le serveur

```bash
python3 -m engine.http --store documents.db --auth engine.auth.TokenAuth --tokens tok_123,dev-token
```

> **Note** : l'exemple ci-dessus utilise un démarrage simplifié. Le point d'entrée
> exact peut varier selon la configuration du projet. Consultez la section
> « Périmètre » pour des ajustements de lancement.

### 1.4 Vérifier que le service tourne

```bash
curl -s http://localhost:8000/health
# {"status":"ok"}
```

---

## 2. Obtenir un token de test

L'API d'authentification accepte un token Bearer. Pour les tests, utilisez l'un
des tokens suivants (configurables au démarrage) :

```bash
# Exemple : token dans l'en-tête Authorization
TOKEN="tok_123"

curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/health
# {"status":"ok"}
```

> **Avertissement** : ne jamais exposer les tokens dans le code source, les
> contrôles de qualité ou les fichiers publiés. Gardez-les côté serveur.

---

## 3. Exemples `curl`

### 3.1 Créer un document

```bash
curl -s -X POST http://localhost:8000/documents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_type": "FACT",
    "numero_serie": 1,
    "org_id": 1,
    "currency": "EUR",
    "retention": 0.0,
    "balance": 0.0
  }'
```

Réponse `201` :

```json
{
  "item": {
    "id": "doc-1a2b3c4d5e6f",
    "doc_type": "FACT",
    "numero_serie": 1,
    "org_id": 1,
    "currency": "EUR",
    "retention": 0.0,
    "balance": 0.0,
    "date_creation": "2026-11-03T00:00:00Z",
    "etat": "brouillon"
  }
}
```

### 3.2 Lister les documents

```bash
curl -s -X GET http://localhost:8000/documents \
  -H "Authorization: Bearer $TOKEN"
```

### 3.3 Lire un document

```bash
curl -s -X GET http://localhost:8000/documents/doc-1a2b3c4d5e6f \
  -H "Authorization: Bearer $TOKEN"
```

### 3.4 Appliquer une transition

```bash
curl -s -X POST http://localhost:8000/documents/doc-1a2b3c4d5e6f/transition \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"etat": "brouillon_pdf"}'
```

---

## 4. Codes d'erreur principaux

| Code | Signification | Quand |
|------|---------------|-------|
| `400` | Bad Request | Requête invalide : champs manquants, règles métier non respectées |
| `401` | Unauthorized | Token absent, invalide, ou mauvais format |
| `404` | Not Found | Document ou route introuvable |
| `405` | Method Not Allowed | Méthode HTTP non autorisée pour le chemin |
| `500` | Internal Server Error | Erreur inattendue côté serveur |

### Exemple d'erreur `401`

```json
{"error": "Unauthorized: missing or invalid token"}
```

### Exemple d'erreur `400` (type invalide)

```json
{"error": "type de document inconnu"}
```

---

## 5. Schémas

Voir le fichier [`openapi.yaml`](./openapi.yaml) pour la spécification complète.

YAML
