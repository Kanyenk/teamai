# Data Model — XoHive

> Schéma de données pour le socle ERP de XoHive.
>
> Basé sur les entités communes définies dans `xohive/docs/architecture/domain-model.md`.

---

## 1. Vue d'ensemble

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Organization│     │     User     │     │    Party     │
└──────────────┘     └──────────────┘     └──────────────┘
       │                      │                   │
       │ ¹                    │ ¹                 │
       ▼                      ▼                   ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Document   │     │    Role      │     │ Permission   │
└──────────────┘     └──────────────┘     └──────────────┘
       │                      │
       ▼                      ▼
┌──────────────┐     ┌──────────────┐
│  Workflow    │     │ AuditEvent   │
└──────────────┘     └──────────────┘
       │
       ▼
┌──────────────┐
│ LedgerEntry  │
└──────────────┘
```

---

## 2. Schémas SQL de base (SQLite)

### Organization

```sql
CREATE TABLE organizations (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    timezone      TEXT,
    currency      TEXT NOT NULL,
    fiscal_code   TEXT,
    website       TEXT,
    phone         TEXT,
    address       TEXT,
    contact_email TEXT,
    created_by    TEXT,
    created_at    TEXT,
    updated_at    TEXT,
    is_active     BOOLEAN NOT NULL DEFAULT 1,
    callback_webhook TEXT
);
```

### User

```sql
CREATE TABLE users (
    id              TEXT PRIMARY KEY,
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    first_name      TEXT,
    last_name       TEXT,
    phone           TEXT,
    timezone        TEXT,
    language        TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT 1,
    is_verified     BOOLEAN NOT NULL DEFAULT 0,
    organisation_id TEXT NOT NULL,
    created_by      TEXT,
    created_at      TEXT,
    updated_at      TEXT,
    FOREIGN KEY (organisation_id) REFERENCES organizations(id)
);
```

### Role

```sql
CREATE TABLE roles (
    id              TEXT PRIMARY KEY,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    organisation_id TEXT NOT NULL,
    permissions     TEXT NOT NULL,
    created_by      TEXT,
    created_at      TEXT,
    updated_at      TEXT,
    FOREIGN KEY (organisation_id) REFERENCES organizations(id)
);
```

### Permission

```sql
CREATE TABLE permissions (
    id          TEXT PRIMARY KEY,
    code        TEXT NOT NULL UNIQUE,
    label       TEXT NOT NULL,
    description TEXT,
    module      TEXT NOT NULL,
    action      TEXT NOT NULL,
    organisation_id TEXT NOT NULL,
    FOREIGN KEY (organisation_id) REFERENCES organizations(id)
);
```

### Document

```sql
CREATE TABLE documents (
    id            TEXT PRIMARY KEY,
    organisation_id TEXT NOT NULL,
    user_id       TEXT,
    doc_type      TEXT NOT NULL,
    numero_serie  INTEGER NOT NULL,
    status        TEXT NOT NULL,
    etat          TEXT NOT NULL,
    hash_etat     TEXT,
    currency      TEXT NOT NULL,
    retention     REAL NOT NULL,
    balance       REAL NOT NULL,
    created_by    TEXT,
    created_at    TEXT,
    updated_at    TEXT,
    FOREIGN KEY (organisation_id) REFERENCES organizations(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Workflow

```sql
CREATE TABLE workflows (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    state_schema    TEXT NOT NULL,
    created_by      TEXT,
    created_at      TEXT,
    updated_at      TEXT
);
```

### WorkflowInstance

```sql
CREATE TABLE workflow_instances (
    id              TEXT PRIMARY KEY,
    workflow_id     TEXT NOT NULL,
    entity_type     TEXT NOT NULL,
    entity_id       TEXT NOT NULL,
    current_state   TEXT NOT NULL,
    metadata        TEXT,
    created_at      TEXT,
    updated_at      TEXT,
    FOREIGN KEY (workflow_id) REFERENCES workflows(id)
);
```

### AuditEvent

```sql
CREATE TABLE audit_events (
    id               TEXT PRIMARY KEY,
    user_id          TEXT,
    organisation_id  TEXT NOT NULL,
    entity_type      TEXT NOT NULL,
    entity_id        TEXT NOT NULL,
    action           TEXT NOT NULL,
    old_values       TEXT,
    new_values       TEXT,
    ip_address       TEXT,
    user_agent       TEXT,
    created_at       TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (organisation_id) REFERENCES organizations(id)
);
```

### LedgerEntry

```sql
CREATE TABLE ledger_entries (
    id              TEXT PRIMARY KEY,
    organisation_id TEXT NOT NULL,
    user_id         TEXT,
    ledger_type     TEXT NOT NULL,
    reference       TEXT NOT NULL,
    debit           REAL NOT NULL,
    credit          REAL NOT NULL,
    balance         REAL NOT NULL,
    doc_id          TEXT,
    created_by      TEXT,
    created_at      TEXT,
    updated_at      TEXT,
    FOREIGN KEY (organisation_id) REFERENCES organizations(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 3. Index recommandés

```sql
CREATE INDEX idx_documents_org ON documents(organisation_id);
CREATE INDEX idx_documents_user ON documents(user_id);
CREATE INDEX idx_audit_org ON audit_events(organisation_id);
CREATE INDEX idx_audit_user ON audit_events(user_id);
CREATE INDEX idx_audit_entity ON audit_events(entity_type, entity_id);
CREATE INDEX idx_ledger_org ON ledger_entries(organisation_id);
CREATE INDEX idx_ledger_type ON ledger_entries(ledger_type);
```

---

## 4. Contraintes d'intégrité

| Contrainte | Règle |
|---|---|
| `users.email` | UNIQUE dans l'ensemble de la table |
| `users.organisation_id` | Doit référencer un `organization` existant |
| `documents.organisation_id` | Doit référencer un `organization` existant |
| `documents.user_id` | Optionnel (NULL si créé par système) |
| `roles.organisation_id` | Doit référencer un `organization` |
| `audit_events.organisation_id` | Doit référencer un `organization` |
| `audit_events.entity_id` | Doit être non NULL |
| `ledger_entries.balance` | Doit être le résultat de `debit - credit` |
| `ledger_entries.organisation_id` | Doit référencer un `organization` |

---

## 5. Types de données

| Type | DDL | Usage |
|---|---|---|
| `TEXT` | `TEXT` | chaînes, UUIDs, dates ISO |
| `INTEGER` | `INTEGER` | numéros de série |
| `REAL` | `REAL` | nombres décimaux (currency, balance) |
| `BOOLEAN` | `BOOLEAN` | actif/inactif |
| `JSON` | `TEXT` | JSON sérialisé (permissions, metadata) |

---

## 6. Exemples de requêtes courantes

### 6.1 Lister les organisations

```sql
SELECT id, name, timezone, currency, is_active, created_at
FROM organizations
WHERE is_active = 1
ORDER BY name
LIMIT 50 OFFSET 0;
```

### 6.2 Lister les documents d'une organisation

```sql
SELECT id, doc_type, numero_serie, etat, balance, created_at
FROM documents
WHERE organisation_id = ?
ORDER BY numero_serie
LIMIT 50 OFFSET 0;
```

### 6.3 Récupérer un utilisateur par email

```sql
SELECT id, email, first_name, last_name, is_active, organisation_id
FROM users
WHERE email = ?;
```

### 6.4 Vérifier si un utilisateur a une permission

```sql
SELECT COUNT(*) AS count
FROM roles
WHERE organisation_id = ?
  AND json_each.value IN (SELECT value FROM json_each(?))
  AND is_active = 1;
```

### 6.5 Audit trail d'une organisation

```sql
SELECT id, user_id, entity_type, entity_id, action, old_values,
       new_values, ip_address, created_at
FROM audit_events
WHERE organisation_id = ?
  AND entity_type = 'Document'
  AND entity_id = ?
ORDER BY created_at DESC
LIMIT 100;
```

---

## 7. Exemples de données

### 7.1 Organisation

```json
{
  "id": "org-1a2b3c4d5e6f",
  "name": "Acme SARL",
  "timezone": "Europe/Paris",
  "currency": "EUR",
  "fiscal_code": "12345678901",
  "website": "https://acme.com",
  "phone": "+33123456789",
  "address": "10 Rue de Rivoli, 75001 Paris",
  "contact_email": "contact@acme.com",
  "created_by": "system",
  "created_at": "2026-11-03T10:00:00Z",
  "updated_at": "2026-11-03T10:00:00Z",
  "is_active": true,
  "callback_webhook": "https://acme.com/webhooks/xohive"
}
```

### 7.2 User

```json
{
  "id": "user-1a2b3c4d5e6f",
  "email": "alice@acme.com",
  "password_hash": "$2b$12$LmQ...",
  "first_name": "Alice",
  "last_name": "Martin",
  "phone": "+33612345678",
  "timezone": "Europe/Paris",
  "language": "fr",
  "is_active": true,
  "is_verified": true,
  "organisation_id": "org-1a2b3c4d5e6f",
  "created_by": "admin",
  "created_at": "2026-11-03T10:00:00Z",
  "updated_at": "2026-11-03T10:00:00Z"
}
```

### 7.3 Role

```json
{
  "id": "role-1a2b3c4d5e6f",
  "code": "admin",
  "label": "Administrateur",
  "description": "Accès complet au module",
  "organisation_id": "org-1a2b3c4d5e6f",
  "permissions": [
    "org:read", "org:write", "user:read", "user:write",
    "doc:read", "doc:create", "doc:update", "doc:delete",
    "audit:read", "ledger:read", "ledger:write"
  ],
  "created_by": "admin",
  "created_at": "2026-11-03T10:00:00Z",
  "updated_at": "2026-11-03T10:00:00Z"
}
```

### 7.4 Permission

```json
{
  "id": "perm-1a2b3c4d5e6f",
  "code": "doc:create",
  "label": "Créer un document",
  "description": "Autorise la création de document",
  "module": "doc",
  "action": "create",
  "organisation_id": "org-1a2b3c4d5e6f"
}
```

### 7.5 Document

```json
{
  "id": "doc-1a2b3c4d5e6f",
  "organisation_id": "org-1a2b3c4d5e6f",
  "user_id": "user-1a2b3c4d5e6f",
  "doc_type": "FACT",
  "numero_serie": 1001,
  "status": "approved",
  "etat": "ecrit",
  "hash_etat": "a1b2c3d4...",
  "currency": "EUR",
  "retention": 0.0,
  "balance": 1000.0,
  "created_by": "alice",
  "created_at": "2026-11-03T10:00:00Z",
  "updated_at": "2026-11-03T10:00:00Z"
}
```

### 7.6 AuditEvent

```json
{
  "id": "ae-1a2b3c4d5e6f",
  "user_id": "user-1a2b3c4d5e6f",
  "organisation_id": "org-1a2b3c4d5e6f",
  "entity_type": "Document",
  "entity_id": "doc-1a2b3c4d5e6f",
  "action": "create",
  "old_values": null,
  "new_values": {
    "id": "doc-1a2b3c4d5e6f",
    "doc_type": "FACT",
    "numero_serie": 1001,
    "etat": "ecrit"
  },
  "ip_address": "192.168.1.42",
  "user_agent": "Mozilla/5.0 (X11; Linux x86_64)",
  "created_at": "2026-11-03T10:00:00Z"
}
```

### 7.7 LedgerEntry

```json
{
  "id": "le-1a2b3c4d5e6f",
  "organisation_id": "org-1a2b3c4d5e6f",
  "user_id": "user-1a2b3c4d5e6f",
  "ledger_type": "sales",
  "reference": "INV-2026-001",
  "debit": 1000.0,
  "credit": 0.0,
  "balance": 1000.0,
  "doc_id": "doc-1a2b3c4d5e6f",
  "created_by": "alice",
  "created_at": "2026-11-03T10:00:00Z",
  "updated_at": "2026-11-03T10:00:00Z"
}
```

---

## 8. Migration(s) prévues

| Mig. # | Contenu | Date |
|---|---|---|
| V1 | Tables `organizations`, `users`, `roles`, `permissions` | 2026-11-03 |
| V2 | Tables `documents`, `workflows`, `workflow_instances` | À venir |
| V3 | Tables `audit_events`, `ledger_entries` | À venir |

---

*Document généré le 2026-11-03. Propriété : XoHive.*
