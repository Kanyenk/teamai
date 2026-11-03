# Overview — XoHive Architecture

> Module XoHive : Documents & Comptabilité
> Version : 1.0

## Objectif du projet

XoHive est une **plateforme ERP modulaire** pour la gestion des entreprises. Ce dépôt contient le module **Documents & Comptabilité**, avec des modules futurs : CRM, Ventes, Achats, Stocks, Projets, RH.

## Architecture générale

```
┌─────────────────────────────────────────────────────────────┐
│  xohive/                                                    │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ docs/                                                 │ │
│  │   architecture/                                       │ │
│  │     overview.md     ← Ceci                            │ │
│  │     domain-model.md │  Entités communes                │ │
│  │     modules.md      │  Rôles des modules               │ │
│  │     api-guidelines.md│  Règles d'API REST              │ │
│  │     data-model.md   │  Modèle de données               │ │
│  │   BACKLOG.md        │  Roadmap (10 tâches)            │ │
│  │   CHARTER.md        │  Positionnement et règles       │ │
│  │   PRODUCT_VISION.md │  Vision produit                  │ │
│  │   HANDOVER.md       │  Transferts d'équipe            │ │
│  └─────────────────────────────────────────────────────────┘ │
│  engine/  ← Module actuel (Documents & Comptabilité v0)      │
│  tests/   ← Suite de tests                                   │
└─────────────────────────────────────────────────────────────┘
```

## Principes d'architecture

1. **Séparation des préoccupations** : chaque module a une responsabilité claire.
2. **Évaporation du code commun** : les entités communes (`Organization`, `User`, `Role`, `Permission`, `Party`, `Document`, `Workflow`, `AuditEvent`, `LedgerEntry`) sont centralisées dans `xohive/domain/`.
3. **Persistence par SQL** : SQLite par défaut, extension possible vers PostgreSQL pour les déploiements prod.
4. **API REST sécurisée** : token Bearer pour l'authentification.
5. **Audit obsolète** : chaque modification d'entité génère un événement d'audit.
6. **Événementiel** : bus d'événements pour la décomposition et les intégrations futures.

## Modules cibles dans XoHive

| Module | Statut | Description |
|---|---|---|
| Documents & Comptabilité | En cours | Cœur de projet actuel |
| CRM | À venir | Contacts, entreprises, opportunités, pipeline, activités |
| Ventes & Facturation | À venir | Devis, factures, paiements |
| Achats | À venir | Commandes, fournisseurs, réapprovisionnement |
| Stocks & WMS | À venir | Gestion des inventaires |
| Projets | À venir | Suivi de projets |
| RH | À venir | Gestion des employés |

## Stack technique

- **Langage** : Python 3.12+
- **Base de données** : SQLite (stdlib `sqlite3`, WAL)
- **Serveur HTTP** : `http.server` (stdlib, sans framework externe)
- **Authentification** : Token Bearer
- **Tests** : `unittest` (stdlib)
- **CI** : GitHub Actions (`.github/workflows/tests.yml`)

---

*Document généré le 2026-11-03. Propriété : XoHive (module Documents & Comptabilité).*
