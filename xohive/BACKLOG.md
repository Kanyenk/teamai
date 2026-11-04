# BACKLOG.md — Socle ERP

> XoHive — Projet privateur d'entreprise. Branche `main` = `e56ebe4` (merge de `docker-deployment`).
>
> **Contexte** : `CHARTER.md` définit le modèle commun requis avant le prochain module (CRM).
> Les 10 premières tâches structurent le **socle ERP** : organisations, utilisateurs, rôles, permissions, audit et événements.

---

## 1. Définir le modèle de données commun (domain model)

**Description** : Créer les entités communes utilisées par tous les modules futurs : `Organization`, `User`, `Role`, `Permission`, `Party`, `Document`, `Workflow`, `AuditEvent`, `LedgerEntry`. Exposer une API Python stable (paquets, interfaces, types).

**Critère d'acceptation** :
- [ ] `xohive/domain/` contient les 9 entités avec les champs définis dans `xohive/docs/architecture/domain-model.md`
- [ ] Tests unitaires couvrant l'initialisation de chaque entité
- [ ] Code coverage > 80% pour ce module
- [ ] Schéma `xohive/docs/architecture/domain-model.md` à jour

**Estimation** : M

---

## 2. Structurer l'organisation d'entreprise (Organization)

**Description** : Créer l'entité `Organization` avec ses attributs (id, nom, timezone, devise par défaut, code fiscal, callback webhook, membres) et les opérations CRUD. Implémenter `OrganizationRepository` (SQLite).

**Critère d'acceptation** :
- [ ] `Organization` initialisable avec `id`, `name`, `timezone`, `currency`, `fiscal_code`, `website`, `phone`, `address`, `contact_email`, `created_by`, `created_at`, `updated_at`
- [ ] `OrganizationRepository.create()`, `get()`, `list()`, `update()`, `delete()`
- [ ] Aptitude à observer `on_create`, `on_update`, `on_delete` callbacks
- [ ] Tests pour chaque opération CRUD

**Estimation** : L

---

## 3. Gestion des utilisateurs (User)

**Description** : Créer l'entité `User` avec ses attributs (id, email, password_hash, first_name, last_name, phone, timezone, language, is_active, is_verified, organisation_id) et les opérations d'authentification (mot de passe hashé avec bcrypt, session token).

**Critère d'acceptation** :
- [ ] `User` initialisable sans exposer le `password_hash` dans les API publiques
- [ ] `UserRepository.create()`, `get()`, `list()`, `update()`, `delete()`
- [ ] Méthode `validate_password()` utilisant bcrypt
- [ ] Méthode `generate_token()` retournant un JWT ou token persistant
- [ ] Tests pour auth (création, validation, update, delete)

**Estimation** : L

---

## 4. Rôles et permissions (Role & Permission)

**Description** : Créer l'entité `Role` (id, code, label, description, organisation_id, permissions: list[str]) et l'entité `Permission` (id, code, label, description, module, action). Implémenter `RoleRepository` et `PermissionRepository`.

**Critère d'acceptation** :
- [ ] Code de permission : `module:action` (ex: `doc:create`, `audit:read`, `ledger:write`)
- [ ] Méthodes `has_permission(user, permission_code)` et `has_role(user, role_code)`
- [ ] `RoleRepository.create()`, `get()`, `list()`, `update()`, `delete()`
- [ ] Tests pour l'attribution de rôles et vérification de permissions

**Estimation** : L

---

## 5. Audit trail — Historique des modifications (AuditEvent)

**Description** : Créer l'entité `AuditEvent` (id, user_id, organisation_id, entity_type, entity_id, action, old_values, new_values, ip_address, user_agent, timestamp) et son repository. Implémenter un hook intégré à `OrganizationRepository`, `UserRepository`, `RoleRepository` et `DocumentRepository`.

**Critère d'acceptation** :
- [ ] Chaque mutation crée un `AuditEvent` avec `old_values` et `new_values`
- [ ] `AuditEventRepository.create()`, `list()`, `get()`
- [ ] Filtres par `organisation_id`, `user_id`, `entity_type`, `entity_id`, `action`
- [ ] Logs dans `data/audit.db` ou dans la même base SQLite
- [ ] Tests couvrant la création, récupération et filtrage

**Estimation** : M

---

## 6. Événements (Events) — Bus d'événements asynchrone

**Description** : Créer le système d'événements (`EventBus`) avec `Event`, `EventType`, `EventSubscriber` et `EventHandler`. Implémenter des events pour `organization.created`, `organization.updated`, `user.created`, `user.deleted`, `role.updated`, `audit.created`.

**Critère d'acceptation** :
- [ ] `EventBus.publish(event)` diffuse à tous les subscribers
- [ ] Support des `sync_handlers` et `async_handlers`
- [ ] `event_bus.subscribe(event_type, handler)`
- [ ] Tests pour publication et souscription
- [ ] Live example: `organization.created` notifie les subscribers

**Estimation** : M

---

## 7. Intégration API HTTP sécurisée (Auth endpoint)

**Description** : Créer les endpoints REST pour les entités du socle : `POST /api/v1/organizations`, `GET /api/v1/organizations`, `GET /api/v1/users`, `POST /api/v1/auth/login`, `GET /api/v1/roles`, `GET /api/v1/audit`. Validation des requêtes avec pydantic, auth Bearer token, pagination.

**Critère d'acceptation** :
- [ ] `POST /api/v1/auth/login` retourne `{access_token, token_type, expires_in, user: {...}}`
- [ ] `GET /api/v1/organizations` liste paginée (limit, offset)
- [ ] Tous les endpoints sauf `/health` et `/auth/login` exigent un token valide
- [ ] Réponses cohérentes en JSON (succès ou `{error: {code, message, details}}`)
- [ ] Tests via `unittest` (30+ tests)

**Estimation** : L

---

## 8. Document model — Document (document domain)

**Description** : Créer l'entité `Document` (id, organisation_id, user_id, doc_type, numero_serie, status, etat, hash_etat, currency, retention, balance, created_by, created_at, updated_at) et son repository. Implémenter les règles métier de validation (doc_type : FACT/BC/BL/NC/RS/CHQ, numero série positif, currency 3 chars, balance ≥ 0, retention 0-1). Intégrer la machine à états (brouillon → brouillon_pdf → envoye → receive → en_cours → execute → ecrit → ferme/annule).

**Critère d'acceptation** :
- [x] `Document` avec champs complets
- [x] `DocumentRepository` (SQLite persisté)
- [x] `DocumentStateMachine` valide les transitions
- [x] `DocumentValidator.validate_creation()` et `validate_transition()`
- [x] Tests pour validation, transitions, repository

**Résultat** :
- Commit: `64098bb` — feat(document): add Document entity and repository
- Merge: `e01285e` — merge: integrate document into main
- Tests: 205/205 OK

**Estimation** : L

---

## 9. Workflow — Machine à états (ERP workflow engine)

**Description** : Créer le module `Workflow` : `WorkflowDefinition` (id, name, state_schema: Dict[str, List[str]], transition_hooks), `WorkflowInstance` (id, workflow_id, current_state, metadata). Implémenter `WorkflowEngine` qui orchestre les transitions et appelle les hooks.

**Critère d'acceptation** :
- [ ] `WorkflowDefinition` définit le schéma des états et transitions
- [ ] `WorkflowInstance` suit l'état courant parmi les états du schéma
- [ ] `WorkflowEngine.transition(instance, new_state)` valide la transition et exécute les hooks
- [ ] Hooks personnalisables (ex: `on_transition_to_ecrit`, `on_transition_to_ferme`)
- [ ] Tests pour validation des transitions, déclenchement des hooks

**Estimation** : M

---

## 10. Ledger — Écritures comptables (LedgerEntry)

**Description** : Créer l'entité `LedgerEntry` (id, organisation_id, user_id, ledger_type, reference, debit, credit, balance, doc_id, created_by, created_at, updated_at) et son repository. Implémenter `Ledger` qui calcule le solde, valide l'équilibre (débit = crédit), et génère des `AuditEvent` sur chaque écriture.

**Critère d'acceptation** :
- [ ] `LedgerEntry` avec champs complets
- [ ] `LedgerRepository` persiste les écritures
- [ ] `Ledger.calculate_balance(organisation_id)` retourne la somme des débits et crédits
- [ ] Écriture avec débit ≠ crédit → `LedgerBalanceError`
- [ ] Tests pour équilibre, création, récupération, calcul de solde

**Estimation** : L

---

## Priorité du socle (ordre recommandé)

| # | Tâche | Estimation |
|---|---|---|
| 1 | Modèle de données commun | M |
| 2 | Organization | L |
| 3 | User | L |
| 4 | Role & Permission | L |
| 5 | AuditEvent | M | ✗ (terminé `db78d8e`, 2026-11-03) |
| 6 | Events | M | ✗ (terminé `adc87fc`, 2026-11-03) |
|| 7 | API HTTP sécurisée | L |
|| 8 | Document | L |
| 9 | Workflow | M |
| 10 | Ledger | L |

---

## Nouveau module : CRM minimal (prochaine priorité)

Module CRM minimal : **entreprises, contacts, opportunités, pipeline, activités**.

> **Dépendances** : tous les modules suivants nécessitent les entités communes du socle ERP
> (Organization, User, Role, Permission) vues aux tâches 1 à 4.

---

## 11. CRM — Entreprise (Company)

**Description** : Créer l'entité `Company` (id, name, siret, address, city, zip_code, country, website, phone, email, contact_person, is_active, created_by, created_at, updated_at) et son repository. Implémenter les règles métier (SIRET format 14 chiffres, email valid, etc.).

**Critère d'acceptation** :
- [ ] `Company` initialisable avec les champs
- [ ] `CompanyRepository` CRUD (create, get, list, update, delete)
- [ ] Validation : SIRET 14 chiffres, email format
- [ ] Tests pour CRUD et validation

**Estimation** : M

**Dépendances** : socle (tâches 1-4), Organisation

---

## 12. CRM — Contact (Contact)

**Description** : Créer l'entité `Contact` (id, first_name, last_name, email, phone, company_id, job_title, is_active, created_by, created_at, updated_at) et son repository. Implémenter le lien N→1 avec Company.

**Critère d'acceptation** :
- [ ] `Contact` initialisable avec les champs
- [ ] `ContactRepository` CRUD
- [ ] Validation : email unique, nom non vide
- [ ] Association avec Company (`company_id`)
- [ ] Tests pour CRUD

**Estimation** : M

**Dépendances** : tâche 11 (Entreprise)

---

## 13. CRM — Opportunité (Opportunity)

**Description** : Créer l'entité `Opportunity` (id, company_id, contact_id, title, amount, stage, probability, close_date, is_active, created_by, created_at, updated_at) et son repository. Implémenter le pipeline d'états (prospecting → qualifier → proposition → négociation → fermé).

**Critère d'acceptation** :
- [ ] `Opportunity` avec les champs
- [ ] `OpportunityRepository` CRUD
- [ ] Machine à états du pipeline
- [ ] Validation : amount > 0, stage dans l'ensemble des états
- [ ] Tests pour CRUD et transitions

**Estimation** : M

**Dépendances** : tâches 11 (Entreprise), 12 (Contact)

---

## 14. CRM — Pipeline (Pipeline)

**Description** : Créer le module `Pipeline` :
- `PipelineDefinition` (id, name, stage_schema)
- `PipelineInstance` (id, pipeline_id, stage, opportunity_id, metadata)
- `PipelineEngine` qui orchestre les transitions de stage

**Critère d'acceptation** :
- [ ] `PipelineDefinition` définit les stages et leurs séquences
- [ ] `PipelineInstance` suit le stage courant
- [ ] `PipelineEngine.transition()` valide et déclenche les hooks
- [ ] Hooks (`on_stage_change`, `on_opportunity_close`)
- [ ] Tests pour transitions et hooks

**Estimation** : M

**Dépendances** : tâche 13 (Opportunité)

---

## 15. CRM — Activité (Activity)

**Description** : Créer l'entité `Activity` (id, company_id, contact_id, user_id, type, subject, description, date, duration, status, is_active, created_by, created_at, updated_at) et son repository. Implémenter les types d'activités (appel, réunion, email, note).

**Critère d'acceptation** :
- [ ] `Activity` avec les champs
- [ ] `ActivityRepository` CRUD
- [ ] Types d'activités valides
- [ ] Associations N→1 : Company, Contact, User
- [ ] Tests pour CRUD

**Estimation** : M

**Dépendances** : tâches 11 (Entreprise), 12 (Contact), 3 (User)

---

## 16. CRM — API REST

**Description** : Créer les endpoints REST pour le module CRM :
- `GET /api/v1/crm/companies`
- `POST /api/v1/crm/companies`
- `GET /api/v1/crm/companies/{id}`
- `PUT /api/v1/crm/companies/{id}`
- `GET /api/v1/crm/contacts`
- `POST /api/v1/crm/contacts`
- `GET /api/v1/crm/contacts/{id}`
- `GET /api/v1/crm/opportunities`
- `POST /api/v1/crm/opportunities`
- `GET /api/v1/crm/opportunities/{id}`
- `GET /api/v1/crm/pipeline/{company_id}`
- `GET /api/v1/crm/activities`
- `POST /api/v1/crm/activities`
- Authentification Bearer, pagination, validation

**Critère d'acceptation** :
- [ ] Tous les endpoints implémentés et testés
- [ ] Auth Bearer sur tous les endpoints
- [ ] Validation des requêtes (pydantic)
- [ ] Réponses JSON cohérentes
- [ ] Tests (30+ tests)

**Estimation** : M

**Dépendances** : tâches 11, 12, 13, 14, 15, 7 (API)

---

## 17. CRM — Audit

**Description** : Implémenter le suivi d'audit pour le module CRM :
- Créer des `AuditEvent` pour les modifications de Company, Contact, Opportunity, Activity
- Hooks intégrés aux repositories CRM
- Compatibilité avec le système d'événements (EventBus)

**Critère d'acceptation** :
- [ ] `AuditEvent` créé pour chaque mutation CRM
- [ ] Filtrage par organisation_id, entity_type, entity_id
- [ ] Compatibilité avec le EventBus
- [ ] Tests pour l'audit CRM

**Estimation** : L

**Dépendances** : tâches 11, 12, 13, 14, 15, 5 (AuditEvent), 6 (Events)

---

## Notes d'architecture

- **Mise en œuvre** : créer le sous-module `xohive/crm/` avec les domaines, repositories et API.
- **Arborescence suggérée** :
  ```
  xohive/crm/
  ├── README.md
  ├── CHARTER.md
  ├── domain/
  │   ├── __init__.py
  │   ├── company.py
  │   ├── contact.py
  │   ├── opportunity.py
  │   ├── pipeline.py
  │   └── activity.py
  ├── repository/
  │   ├── __init__.py
  │   ├── company_repository.py
  │   ├── contact_repository.py
  │   ├── opportunity_repository.py
  │   ├── pipeline_repository.py
  │   └── activity_repository.py
  ├── api/
  │   ├── __init__.py
  │   └── v1/
  │       ├── __init__.py
  │       ├── companies.py
  │       ├── contacts.py
  │       ├── opportunities.py
  │       ├── pipeline.py
  │       └── activities.py
  └── tests/
      └── test_crm.py
  ```
- **Validation** : lancer tous les tests (`.venv/bin/python -m unittest discover -s tests -v`) avant le commit.
