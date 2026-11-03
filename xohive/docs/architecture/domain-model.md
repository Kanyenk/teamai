# Domain Model — XoHive

> Modèle de données commun pour le socle ERP de XoHive.
>
> Les entités suivantes doivent être implémentées dans `xohive/domain/` avant le prochain module (CRM).

---

## Énumération des entités

| Entité | Description | Type |
|---|---|---|
| `Organization` | Entreprise / organisation cliente | Composite |
| `User` | Utilisateur de la plateforme | Composite |
| `Role` | Rôle avec permissions | Composite |
| `Permission` | Permission (module:action) | Leaf |
| `Party` | Père commun : Organisation + Utilisateur | Abstract |
| `Document` | Document comptable / PDF | Composite |
| `Workflow` | Machine à états | Leaf |
| `AuditEvent` | Evénement d'audit | Leaf |
| `LedgerEntry` | Écriture comptable | Leaf |

---

## Entity : Organization

| Champ | Type | NULL | Description |
|---|---|---|---|
| `id` | TEXT/UUID | NO | Identifiant unique |
| `name` | TEXT | NO | Nom de l'entreprise |
| `timezone` | TEXT | YES | Fuseau horaire (ex: `Europe/Paris`) |
| `currency` | TEXT | NO | Devise par défaut (ex: `EUR`) |
| `fiscal_code` | TEXT | YES | Code fiscal / SIREN |
| `website` | TEXT | YES | Site web |
| `phone` | TEXT | YES | Téléphone |
| `address` | TEXT | YES | Adresse |
| `contact_email` | TEXT | YES | Email de contact |
| `created_by` | TEXT | YES | Créé par |
| `created_at` | DATETIME | YES | Date de création |
| `updated_at` | DATETIME | YES | Dernière mise à jour |
| `is_active` | BOOLEAN | NO | Actif/inactif |
| `callback_webhook` | TEXT | YES | Webhook d'événements |

**Relations** : `1 → N` avec `User`, `Document`, `AuditEvent`, `LedgerEntry`.

---

## Entity : User

| Champ | Type | NULL | Description |
|---|---|---|---|
| `id` | TEXT/UUID | NO | Identifiant unique |
| `email` | TEXT | NO | Email (unique) |
| `password_hash` | TEXT | NO | Hash bcrypt |
| `first_name` | TEXT | YES | Prénom |
| `last_name` | TEXT | YES | Nom |
| `phone` | TEXT | YES | Téléphone |
| `timezone` | TEXT | YES | Fuseau horaire |
| `language` | TEXT | YES | Langue (ex: `fr`) |
| `is_active` | BOOLEAN | NO | Actif/inactif |
| `is_verified` | BOOLEAN | NO | Email vérifié |
| `organisation_id` | TEXT | NO | Organisation de rattachement |
| `created_by` | TEXT | YES | Créé par |
| `created_at` | DATETIME | YES | Date de création |
| `updated_at` | DATETIME | YES | Dernière mise à jour |

**Relations** : `N → 1` Organisation, `1 → N` Roles, `1 → N` AuditEvent.

---

## Entity : Role

| Champ | Type | NULL | Description |
|---|---|---|---|
| `id` | TEXT/UUID | NO | Identifiant unique |
| `code` | TEXT | NO | Code (ex: `admin`, `worker`, `auditor`) |
| `label` | TEXT | NO | Libellé français |
| `description` | TEXT | YES | Description |
| `organisation_id` | TEXT | NO | Organisation |
| `permissions` | TEXT | NO | Listes des codes de permission (JSON) |
| `created_by` | TEXT | YES | Créé par |
| `created_at` | DATETIME | YES | Date de création |
| `updated_at` | DATETIME | YES | Dernière mise à jour |

**Relations** : `N → 1` Organisation, `N → 1` User.

---

## Entity : Permission

| Champ | Type | NULL | Description |
|---|---|---|---|
| `id` | TEXT/UUID | NO | Identifiant unique |
| `code` | TEXT | NO | Code `module:action` (ex: `doc:create`) |
| `label` | TEXT | NO | Libellé français |
| `description` | TEXT | YES | Description |
| `module` | TEXT | NO | Module (ex: `doc`, `audit`, `ledger`) |
| `action` | TEXT | NO | Action (ex: `create`, `read`, `write`) |
| `organisation_id` | TEXT | NO | Organisation |

**Relations** : `1 → N` Role (via `permissions` JSON).

---

## Entity : Party (abstrait)

`Party` est une entité parente abstraite pour les entités `Organization` et `User`. Elle définit les champs communs :

| Champ | Type | NULL | Description |
|---|---|---|---|
| `id` | TEXT/UUID | NO | Identifiant unique |
| `created_by` | TEXT | YES | Créé par |
| `created_at` | DATETIME | YES | Date de création |
| `updated_at` | DATETIME | YES | Dernière mise à jour |
| `is_active` | BOOLEAN | NO | Actif/inactif |

`Party` n'est pas une table SQLite ; elle sert de modèle d'architecture uniquement.

---

## Entity : Document

| Champ | Type | NULL | Description |
|---|---|---|---|
| `id` | TEXT/UUID | NO | Identifiant unique |
| `organisation_id` | TEXT | NO | Organisation |
| `user_id` | TEXT | YES | Créé par (utilisateur) |
| `doc_type` | TEXT | NO | Type (FACT, BC, BL, NC, RS, CHQ) |
| `numero_serie` | INTEGER | NO | Numéro de série |
| `status` | TEXT | NO | Statut (`draft`, `sent`, `received`, `approved`, `rejected`) |
| `etat` | TEXT | NO | État (machine à états) |
| `hash_etat` | TEXT | YES | Haché SHA-256 de l'état |
| `currency` | TEXT | NO | Devise |
| `retention` | DECIMAL | NO | Taux de rétention (0-1) |
| `balance` | DECIMAL | NO | Solde |
| `created_by` | TEXT | YES | Créé par |
| `created_at` | DATETIME | YES | Date de création |
| `updated_at` | DATETIME | YES | Dernière mise à jour |

**Relations** : `N → 1` Organisation, `N → 1` User, `1 → N` AuditEvent.

---

## Entity : Workflow

| Champ | Type | NULL | Description |
|---|---|---|---|
| `id` | TEXT/UUID | NO | Identifiant unique |
| `name` | TEXT | NO | Nom (ex: `invoice_workflow`) |
| `state_schema` | TEXT | NO | Schéma des états (JSON) |
| `created_by` | TEXT | YES | Créé par |
| `created_at` | DATETIME | YES | Date de création |
| `updated_at` | DATETIME | YES | Dernière mise à jour |

**Relations** : `1 → N` WorkflowInstance.

---

## Entity : WorkflowInstance

| Champ | Type | NULL | Description |
|---|---|---|---|
| `id` | TEXT/UUID | NO | Identifiant unique |
| `workflow_id` | TEXT | NO | Workflow auquel il appartient |
| `entity_type` | TEXT | NO | Type d'entité (Document, Invoice…) |
| `entity_id` | TEXT | NO | ID de l'entité liée |
| `current_state` | TEXT | NO | État courant |
| `metadata` | TEXT | YES | Métadonnées JSON |
| `created_at` | DATETIME | YES | Date de création |
| `updated_at` | DATETIME | YES | Dernière mise à jour |

**Relations** : `1 → 1` Workflow definition (via `workflow_id`).

---

## Entity : AuditEvent

| Champ | Type | NULL | Description |
|---|---|---|---|
| `id` | TEXT/UUID | NO | Identifiant unique |
| `user_id` | TEXT | YES | Utilisateur (NULL si système) |
| `organisation_id` | TEXT | NO | Organisation |
| `entity_type` | TEXT | NO | Type d'entité modifiée |
| `entity_id` | TEXT | NO | ID de l'entité |
| `action` | TEXT | NO | Action (`create`, `update`, `delete`, `transition`) |
| `old_values` | TEXT | YES | Valeurs avant (JSON) |
| `new_values` | TEXT | YES | Nouvelles valeurs (JSON) |
| `ip_address` | TEXT | YES | IP source |
| `user_agent` | TEXT | YES | User-Agent |
| `created_at` | DATETIME | NO | Horodatage |

**Relations** : `N → 1` Organisation, `N → 1` User.

---

## Entity : LedgerEntry

| Champ | Type | NULL | Description |
|---|---|---|---|
| `id` | TEXT/UUID | NO | Identifiant unique |
| `organisation_id` | TEXT | NO | Organisation |
| `user_id` | TEXT | YES | Utilisateur |
| `ledger_type` | TEXT | NO | Type (`opening`, `sales`, `purchase`, `expense`, `payment`) |
| `reference` | TEXT | NO | Référence interne |
| `debit` | DECIMAL | NO | Débit |
| `credit` | DECIMAL | NO | Crédit |
| `balance` | DECIMAL | NO | Solde après écriture |
| `doc_id` | TEXT | YES | Document lié (Journal, Invoice…) |
| `created_by` | TEXT | YES | Créé par |
| `created_at` | DATETIME | YES | Date de création |
| `updated_at` | DATETIME | YES | Dernière mise à jour |

**Relations** : `N → 1` Organisation, `N → 1` User.

---

## Règles de validation

| Entité | Règle |
|---|---|
| Organization | `name` non vide, `currency` code ISO 3 |
| User | `email` unique, `password_hash` non vide |
| Role | `code` unique dans l'organisation |
| Permission | `code` unique globalement |
| Document | `doc_type` dans {FACT, BC, BL, NC, RS, CHQ}, `numero_serie` > 0, `balance` ≥ 0 |
| Workflow | `state_schema` valide (au moins un état) |
| AuditEvent | `entity_type` et `entity_id` non vides |
| LedgerEntry | `debit = credit` (équilibre imposé) |

---

## Flux d'héritage

```
Party (abstrait)
├─ Organization
└─ User
    ├─ Role (1→N)
    │   └─ Permission (via JSON)
    └─ Document (N→1)
        ├─ WorkflowInstance (N→1)
        └─ AuditEvent (N→1)
            └─ LedgerEntry (N→1)
```

---

*Document généré le 2026-11-03. Propriété : XoHive.*
