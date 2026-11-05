Codées à partir de la documentation technique.

---

## 3. Configuration du module CRM

Le module CRM est accessible sur le port 8081 avec les routes `/api/v1/crm/*`.

### Variables d'environnement

| Variable | Description | Valeur exemple |
|----------|-------------|----------------|
| `TEAMAI_TOKENS` | Tokens d'authentification pour CRM | `tok_123,dev-token` |
| `TEAMAI_DB_PATH` | Chemin vers la base CRM | `/opt/projects/teamai/data/teamai.db` |

### Démarrage du serveur CRM

```bash
cd /opt/projects/teamai
TEAMAI_TOKENS="tok_123,dev-token" \
  python3 -m engine.http \
    --host 0.0.0.0 \
    --port 8081 \
    --db data/teamai.db
```

---

## 4. Documentation de l'API CRM

### Endpoints disponibles

#### Companies

| Méthode | Chemin | Description |
|---------|--------|-------------|
| GET | `/api/v1/crm/companies` | Lister les entreprises |
| POST | `/api/v1/crm/companies` | Créer une entreprise |
| GET | `/api/v1/crm/companies/{id}` | Récupérer une entreprise |

#### Contacts

| Méthode | Chemin | Description |
|---------|--------|-------------|
| GET | `/api/v1/crm/contacts` | Lister les contacts |
| POST | `/api/v1/crm/contacts` | Créer un contact |
| GET | `/api/v1/crm/contacts/{id}` | Récupérer un contact |

#### Opportunities

| Méthode | Chemin | Description |
|---------|--------|-------------|
| GET | `/api/v1/crm/opportunities` | Lister les opportunités |
| POST | `/api/v1/crm/opportunities` | Créer une opportunité |
| GET | `/api/v1/crm/opportunities/{id}` | Récupérer une opportunité |

#### Pipeline

| Méthode | Chemin | Description |
|---------|--------|-------------|
| GET | `/api/v1/crm/pipeline/{company_id}` | Récupérer le pipeline |

#### Activities

| Méthode | Chemin | Description |
|---------|--------|-------------|
| GET | `/api/v1/crm/activities` | Lister les activités |
| POST | `/api/v1/crm/activities` | Créer une activité |

### Exemples de requêtes

#### Créer une entreprise

```bash
curl -X POST http://localhost:8081/api/v1/crm/companies \
  -H "Authorization: Bearer tok_123" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme SARL",
    "siret": "12345678901234",
    "city": "Paris",
    "zip_code": "75001",
    "country": "FR",
    "organisation_id": "default-org"
  }'
```

#### Lister les opportunités

```bash
curl -X GET http://localhost:8081/api/v1/crm/opportunities \
  -H "Authorization: Bearer tok_123"
```

#### Créer une activité

```bash
curl -X POST http://localhost:8081/api/v1/crm/activities \
  -H "Authorization: Bearer tok_123" \
  -H "Content-Type: application/json" \
  -d '{
    "organisation_id": "default-org",
    "company_id": "crm-756253312ee0",
    "contact_id": "crm-8111e1c64bfd",
    "type": "appel",
    "subject": "Appel prospectif",
    "status": "done"
  }'
```

---

## 5. Gestion des données CRM

### Les données sont stockées dans SQLite

La base de données est située à : `data/teamai.db`

**Tables CRM** :
- `crm_companies` : entreprises
- `crm_contacts` : contacts
- `crm_opportunities` : opportunités
- `crm_activities` : activités
- `crm_audit_events` : événements d'audit

### Vérifier l'intégrité de la base

```bash
sqlite3 data/teamai.db "PRAGMA integrity_check;"
```

### Sauvegarde de la base

```bash
cp data/teamai.db data/teamai.db.backup-$(date +%Y%m%d)
```

---

## 6. Gestion des erreurs

### Codes d'erreur courants

| Code | Description | Solution |
|------|-------------|----------|
| 400 | Données invalides | Vérifier le format des champs |
| 401 | Token manquant/invalide | Vérifier `TEAMAI_TOKENS` et l'en-tête `Authorization` |
| 404 | Ressource introuvable | Vérifier l'ID de la ressource |
| 500 | Erreur serveur | Vérifier les logs dans `data/server.log` |

### Vérifier les logs

```bash
tail -f data/server.log
```

---

## 7. Mise à jour de la documentation

- **API.md** : mise à jour avec les nouvelles routes CRM
- **RUNBOOK.md** : guide d'exploitation pour le module CRM
- **BACKLOG.md** : tâches en cours pour le module Ventes & Facturation

---

## 8. Références

- **API REST** : voir `API.md` pour la documentation complète
- **Architecture** : voir `xohive/docs/` pour la description de l'architecture
- **Backlog** : voir `xohive/BACKLOG.md` pour les tâches en cours

---

