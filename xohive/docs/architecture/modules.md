# Modules — XoHive Architecture

> Mappage des modules physiques, leurs rôles et leurs dépendances.

---

## Table des matières

- [Modules principaux](#modules-principaux)
- [Dépôt de code](#dépôt-de-code)
- [Plan de structure](#plan-de-structure)
- [Dépendances entre modules](#dépendances-entre-modules)

---

## Modules principaux

### Module : XoHive

| Attribut | Valeur |
|---|---|
| Dossier | `xohive/` |
| Fichier racine | `CHARTER.md` |
| Vision produit | `PRODUCT_VISION.md` |
| Handover | `HANDOVER.md` |
| Backlog | `BACKLOG.md` |
| Architecture | `docs/architecture/` |

**Description** : Plateforme ERP modulaire. Module Documents & Comptabilité.

**Composants du module** :
- `engine/` — Moteur de documents et comptabilité (v0)
- `docs/` — Documentation technique (OpenAPI, HTTP API, architecture)
- `tests/` — Suite de tests
- `data/` — Base de données et logs

---

## Architecture complète

```
┌──────────────────────────────────────────────────────────────┐
│  xohive/                                                     │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  CHARTER.md    — Positionnement et règles              │ │
│  │  PRODUCT_VISION.md — Vision produit du projet          │ │
│  │  HANDOVER.md   — Transferts d'équipe                   │ │
│  │  BACKLOG.md    — Roadmap (10 tâches)                   │ │
│  │  domain/       — (classé, non encore implémenté)      │ │
│  │  docs/         — Documentation                         │ │
│  │    architecture/  — Architecture du module             │ │
│  └──────────────────────────────────────────────────────────┘ │
│  engine/                                                     │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  __init__.py     — État, Document, transitions          │ │
│  │  api.py        — API minimale                         │ │
│  │  auth.py       — TokenAuth                            │ │
│  │  documents.py  — DocumentStore, DocumentEditor        │ │
│  │  repository.py — DocumentRepository (SQLite)            │ │
│  │  http.py       — HttpHandler, make_app, main           │ │
│  │  exceptions.py — Exceptions métier                      │ │
│  │  ledger.py     — Ledger                               │ │
│  │  transactions.py — TransactionStore                   │ │
│  │  validation.py — DocumentValidator                    │ │
│  └──────────────────────────────────────────────────────────┘ │
│  tests/                                                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  test_*.py — 90 tests unitaires                        │ │
│  └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## Plan de structure recommandé pour les nouveaux modules

Chaque module futur (CRM, Ventes, etc.) suivra ce schéma :

```
xohive/<module>/
├── README.md
├── CHARTER.md
├── PRODUCT_VISION.md
├── HANDOVER.md
├── BACKLOG.md
├── domain/
│   ├── __init__.py
│   ├── organization.py
│   ├── user.py
│   ├── role.py
│   ├── permission.py
│   ├── party.py (abstrait)
│   ├── document.py
│   ├── workflow.py
│   ├── audit_event.py
│   └── ledger_entry.py
├── repository/
│   ├── __init__.py
│   ├── organization_repository.py
│   ├── user_repository.py
│   ├── role_repository.py
│   ├── permission_repository.py
│   ├── document_repository.py
│   ├── workflow_repository.py
│   ├── audit_event_repository.py
│   └── ledger_entry_repository.py
├── service/
│   ├── __init__.py
│   ├── organization_service.py
│   ├── user_service.py
│   ├── role_service.py
│   ├── document_service.py
│   ├── workflow_service.py
│   ├── audit_service.py
│   └── ledger_service.py
├── api/
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── organizations.py
│   │   ├── users.py
│   │   ├── roles.py
│   │   ├── documents.py
│   │   ├── workflows.py
│   │   ├── audit.py
│   │   └── ledger.py
│   └── auth.py
└── tests/
    └── test_<module>.py

xohive/<module>/docs/
└── architecture/
    ├── overview.md
    ├── domain-model.md
    ├── modules.md
    ├── api-guidelines.md
    └── data-model.md
```

---

## Dépendances entre modules

```
┌──────────────┐     ┌──────────────┐
│  Organization │ ←── │      User    │
└──────────────┘     └──────────────┘
       │
       │ ¹          ²
       ▼
┌──────────────┐     ┌──────────────┐
│   Document   │ ←── │    Workflow  │
└──────────────┘     └──────────────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│  AuditEvent  │ ←── │  LedgerEntry │
└──────────────┘     └──────────────┘
```

**Liens** :
1. `Organization` a un `User` par `organisation_id`.
2. `Document` appartient à une `Organization` et est créé par un `User`.
3. `Workflow` est lié à un `Document` ou à une entité générique.
4. `AuditEvent` trace les modifications de `Organization`, `User`, `Document`, `Workflow`.
5. `LedgerEntry` trace les écritures comptables et peut être lié à un `Document`.

---

## Modules de support

| Module | Fichier | Rôle |
|---|---|---|
| `engine` | `engine/http.py` | Serveur HTTP, gestionnaire de requêtes |
| `engine` | `engine/repository.py` | SQLite repository pour `Document` |
| `engine` | `engine/auth.py` | Authentification Bearer |
| `engine` | `engine/validation.py` | Règles métier de validation |
| `engine` | `engine/exceptions.py` | Exceptions métier |
| `engine` | `engine/ledger.py` | Moteur d'écriture comptable |
| `.github/workflows/tests.yml` | CI GitHub Actions |

---

*Document généré le 2026-11-03. Propriété : XoHive.*
