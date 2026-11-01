---
title: "02 — Moteur de documents : spécification technique V0"
date: 2026-11-02
type: "technique"
tags: [xohive, technique, moteur, documents, machine-etats, base-de-donnees]
source: "[[Charte]]; [[01-machine-documents]]"
---

# 02 — Moteur de documents et modèle de données — Spécification technique V0

## 1. Synthese

Le socle V0 de XoHive est un **moteur de documents événementiels** :
une machine à états parcourue sans trou, propre à l'immuabilité et tracée.
Le module produit (v0) n'est pas un ERP complet : c'est le socle avec lequel on
peut faire traverser un document fictif tout le flux — brouillon, PDF, écriture
équilibrée, chaîne de hachage — sans intervention manuelle.

Cet ensemble est découpé en trois sous-modules :

| Sous-module | Description | Livrable V0 |
|---|---|---|
| **S1 — Machine à états** | États, transitions, invariants | ✅ `docs/technique/01-machine-documents.md` |
| **S2 — Modèle de données** | Base, schéma, réf. V1 | à livrer (ce fichier) |
| **S3 — Traducteur + PDF + flux** | Écriture, hachage, projection, édition PDF | à livrer (suivi) |

## 2. Modèle de données — Base et schéma

### 2.1 Principe

La base est une **base événementielle** : chaque écriture est tracée, chaque
objet est immuable. Aucune colonne n'est modifiée après validation ; toute
modification crée une ligne nouvelle.

Le schéma SQL ci-dessous est la spécification de la version V0. Il est écrit
pour PostgreSQL (le socle technique par défaut) et est compatible avec tout
moteur SQL polyglotte (c'est la règle du socle).

### 2.2 Schéma SQL (PostgreSQL)

```sql
-- XoHive — socle V0 — schéma de base
-- Version : 0.1 — prêté pour le prototypage (v0.2+ : génération auto)
-- Auteur : TeamAI / agent engineer

BEGIN;

-- ============================================================
-- 1. Référentiels V1 (fournis, sans modification)
-- ============================================================

CREATE TABLE reference_comptes (
  id          BIGSERIAL PRIMARY KEY,
  code        TEXT NOT NULL,          -- libellé du compte (ex. 1110)
  libelle     TEXT NOT NULL,
  nature      TEXT NOT NULL CHECK (nature IN ('actif','passif','charge','produit','autre')),
  solde       NUMERIC(18,4) DEFAULT 0,  -- débit statistique : solde = somme débit(s) - somme crédit(s)
  ORGANIGNE   BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE reference_unites (
  id          BIGSERIAL PRIMARY KEY,
  code        TEXT NOT NULL,
  libelle     TEXT NOT NULL
);

CREATE TABLE reference_tiers (
  id          BIGSERIAL PRIMARY KEY,
  siret       TEXT,                     -- optionnel, nil si fournisseur/interne
  denomination TEXT NOT NULL,
  type        TEXT NOT NULL,            -- TOUCHE, Fournisseur, Associé, Personnel
  adresse     TEXT,
  telephone   TEXT,
  mail        TEXT
);

CREATE TABLE reference_taxes (
  id          BIGSERIAL PRIMARY KEY,
  code        TEXT NOT NULL,            -- ex. TVA0, TVA10, TVA20, TVA50, NON_TAXABLE
  taux        NUMERIC(5,4),             -- NULL si non applicable
  libelle     TEXT NOT NULL
);

CREATE TABLE reference_devises (
  id          BIGSERIAL PRIMARY KEY,
  code        TEXT NOT NULL,            -- ISO 4217 (EUR, USD, ...)
  symbole     TEXT NOT NULL
);

-- ============================================================
-- 2. Division et organisation
-- ============================================================

CREATE TABLE org (
  id          BIGSERIAL PRIMARY KEY,
  siren       TEXT NOT NULL UNIQUE,
  denomination TEXT NOT NULL,
  sigle       TEXT,
  num_ape     TEXT,
  adresse     TEXT,
  alimentation_court IS TEXT
);

-- ==================================================================
-- 3. Documents
-- ==================================================================

CREATE TABLE doc_type (
  id          BIGSERIAL PRIMARY KEY,
  code        TEXT NOT NULL UNIQUE,     -- FACT, BC, BL, NC, RR, R, ...
  libelle     TEXT NOT NULL,
  nature      TEXT NOT NULL,            -- ENTRANTE, SORTANTE, VERSEMENT, STOCK
  is_vente    BOOLEAN DEFAULT FALSE,
  is_achat    BOOLEAN DEFAULT FALSE,
  est_stock   BOOLEAN DEFAULT FALSE
);

CREATE TABLE document (
  id          BIGSERIAL PRIMARY KEY,
  org_id      BIGINT NOT NULL REFERENCES org(id) ON DELETE RESTRICT,
  type_id     BIGINT NOT NULL REFERENCES doc_type(id),
  num         TEXT NOT NULL,            -- numéro de série (ou affiché)
  ref         TEXT,                     -- référence client/fournisseur
  date_creation TIMESTAMP NOT NULL DEFAULT now(),
  date_echeance TIMESTAMP,              -- défini pour les factures
  date_ecoulement TIMESTAMP,            -- défini à la réception / échéance
  date_pdf    TIMESTAMP,
  etat_id     BIGINT NOT NULL,          -- état courant (voir état table)
  numero_serie BIGINT,                  -- séquence
  somme_ttc   NUMERIC(18,4) NOT NULL,
  somme_ht    NUMERIC(18,4) NOT NULL,
  tva_total   NUMERIC(18,4) NOT NULL,
  currency    TEXT NOT NULL DEFAULT 'EUR',  -- ISO 4217
  balance     NUMERIC(18,4) NOT NULL,   -- solde du document par rapport au calcul (étalon)
  retention   NUMERIC(5,4) DEFAULT 0,   -- taux de rétention éventuel
  is_supprime BOOLEAN NOT NULL DEFAULT FALSE, -- purge logique
  -- hachage de vérification
  hash_etat   TEXT NOT NULL,            -- signature de l'état courant
  hash_pdf    TEXT,                     -- hash du fichier PDF généré
  created_by  TEXT NOT NULL,            -- identifiant de l'acteur
  updated_by  TEXT NOT NULL,
  created_at  TIMESTAMP NOT NULL DEFAULT now(),
  updated_at  TIMESTAMP NOT NULL DEFAULT now()
);

-- Référence document + état
CREATE TABLE document_etat (
  id          BIGSERIAL PRIMARY KEY,
  document_id BIGINT NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  etat_id     BIGINT NOT NULL,
  date_etat   TIMESTAMP NOT NULL DEFAULT now(),
  acteur      TEXT NOT NULL,
  utilisateur TEXT
);

-- ==================================================================
-- 4. États de document
-- ==================================================================

CREATE TABLE etat (
  id          BIGSERIAL PRIMARY KEY,
  code        TEXT NOT NULL UNIQUE,     -- brouillon, brouillon_pdf, envoyé, en_cours, exécuté, écrit, fermé, annulé, supprimé
  libelle     TEXT NOT NULL,
  ordre       INTEGER NOT NULL,         -- ordre de la machine à états
  is_final    BOOLEAN NOT NULL DEFAULT FALSE,
  notion      TEXT,                     -- libellé court
  CONSTRAINT uniq_etat_code UNIQUE (code)
);

-- ==================================================================
-- 5. Écritures comptables (moteur)
-- ==================================================================

CREATE TABLE ecriture (
  id          BIGSERIAL PRIMARY KEY,
  org_id      BIGINT NOT NULL REFERENCES org(id) ON DELETE RESTRICT,
  date_ecriture TIMESTAMP NOT NULL DEFAULT now(),
  libelle     TEXT,
  est_zero    BOOLEAN NOT NULL DEFAULT FALSE,
  hash_global TEXT NOT NULL,            -- hachage de la totalité de l'écriture
  created_by  TEXT NOT NULL,
  updated_by  TEXT NOT NULL,
  created_at  TIMESTAMP NOT NULL DEFAULT now(),
  updated_at  TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE ecriture_ligne (
  id          BIGSERIAL PRIMARY KEY,
  ecriture_id BIGINT NOT NULL REFERENCES ecriture(id) ON DELETE CASCADE,
  compte_id   BIGINT NOT NULL REFERENCES reference_comptes(id),
  debit       NUMERIC(18,4) NOT NULL DEFAULT 0,
  credit      NUMERIC(18,4) NOT NULL DEFAULT 0,
  devise      TEXT NOT NULL DEFAULT 'EUR',
  CONSTRAINT check_debit_credit CHECK (debit >= 0 AND credit >= 0)
);

-- Index pour la recherche de transactions
CREATE INDEX idx_ecriture_org ON ecriture(org_id);
CREATE INDEX idx_ecrire_ligne_compte ON ecrire_ligne(compte_id);
CREATE INDEX idx_doc_etat_etat ON document_etat(etat_id);

COMMIT;
```

### 2.3 Vérification de l'import

Le schéma est vérifiable par un import PostgreSQL avec un super-utilisateur (ou
un super-utilisateur avec les droits requis) :

```bash
createdb -U utilisateur xohive_v0
psql -U utilisateur -d xohive_v0 -f docs/technique/schéma.sql
```

## 3. Moteur de documents — logique

### 3.1 Architecture

Le moteur est divisé en trois couches :

| Couche | Rôle |
|---|---|
| **Documents** | Lecture, création, séquencement et gestion des métadonnées |
| **Écriture** | Génération des écritures comptables à partir d'un document |
| **Hachage** | Chaîne de hachage de la totalité du flux |

### 3.2 Séquence d'exécution

Chaque document suit la séquence suivante :

```
brouillon → brouillon_pdf → envoyé → en_cours → exécuté → écrit → fermé
```

Chaque transition est décrite dans `01-machine-documents.md`.

### 3.3 Calcul du solde

Le solde d'un document est la différence entre le débit et le crédit des lignes :
le calcul est fait par les lignes créées automatiquement à partir du document.

```python
def solde_formulaire(somme_ttc, somme_ht, tva_total, retention):
    """Calcule le solde et le taux de retenue."""

    # L'entrée brute (exemple : facture client TTC)
    montant = somme_ttc

    # Application de la rétention (ex. 0% = pas de rétention)
    if retention > 0:
        montant = montant * (1 - retention)

    # Le solde = montant + tva + (retention si applicable)
    solde = montant + tva_total
    return solde, taux_retention
```

### 3.4 Calendier de sortie

Le calendrier est défini par les dates de l'écriture :
date de création, échéance, échéance, et échéance d'expiration.

```python
def calendrier_solde(date_creation, date_echeance, date_ecoulement):
    from datetime import date
    now = date.today()

    calendrier = {
        "creation": date_creation,
        "echeance": date_echeance,
        "ecoulement": date_ecoulement,
        "vencu": None,
        "expire": None
    }

    if date_echeance and date_echeance < now:
        calendrier["vencu"] = date_echeance

    if date_echeance and date_echeance < now + timedelta(days=90):
        calendrier["vencu"] = date_echeance

    if date_echeance and date_echeance >= now + timedelta(days=90):
        calendrier["expire"] = date_echeance

    return calendrier
```

### 3.5 Tests

Le flux document → écriture → hachage est testé automatiquement par le module
de test.

Pour le prototypage, le test vérifie que :

- le solde d'un document est bien un nombre positif ou nul ;
- le taux de rétention est bien compris entre 0 et 1 ;
- la chaîne de hachage est bien recalculée après une écriture ;
- le document est modifié correctement.

## 4. Règles de gestion

| Règle | Description |
|---|---|
| RG1 | Chaque document a une machine à états et une séquence sans trou |
| RG2 | Un document peut être ouvert en lecture seule après son état `écrit` |
| RG3 | Le solde d'un document est calculé sur demande |
| RG4 | Le document est modifié si et seulement si l'état est `brouillon` |
| RG5 | L'état `brouillon_pdf` génère une référence PDF |
| RG6 | Le calcul de la chaîne de hachage est effectué à chaque étape |
| RG7 | Le test automatique du flux est exécuté avant chaque publication |
| RG8 | Un document `fermé` ne peut plus être modifié |

## 5. Interface

L'interface est une API REST exposée à travers un proxy d'image.
Chaque appel API appelle le moteur et renvoie la réponse.

**Endpoint principal :** `/api/v0/documents`

**Méthode GET :** liste les documents d'un organisme

```
GET /api/v0/documents?org_id=1&etat_id=1&offset=0&limit=10
```

**Réponse :**

```json
[
  {
    "id": 1,
    "org_id": 1,
    "type_id": 1,
    "num": "FR-2026-001",
    "date_creation": "2025-11-20T09:35:00.000Z",
    "etat_id": 2,
    "num_serie": 1
  },
  ...
]
```

## 6. Dépendances externes

| Dépendance | Rôle |
|---|---|
| FreeLLMAPI | LLM local servant le moteur |
| PostgreSQL | Base de données du moteur |
| image/PDF | Génération du PDF et du fichier de sortie |
| API REST | Interface externe |

## 7. Notes

- Le moteur est un socle : il ne dépend d'aucun framework métier.
- Toutes les règles métier sont définies dans `01-machine-documents.md` et
  `02-schema-sql.md`.
- La chaîne de hachage est recalculée à chaque étape et est immuable.
- Les tests vous sont donnés pour vous aider à vérifier le flux et ne sont pas
  une contrainte.
