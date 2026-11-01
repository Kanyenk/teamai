---
title: "01 — Fiche-cadre produit XoHive"
date: 2026-11-02
type: "direction"
tags: [xohive, produit, canvas, direction]
source: "[[Charte]]; [[xohive_presentation]]"
---

# XoHive — Fiche-cadre produit (V0)

*Agent `product-founder`. Base : charte XoHive + fiche d'identité. Tout chiffre non
énuméré ici est une hypothèse.*

## 1. En une phrase

**XoHive est un produit SaaS d'ERP + CRM pour les PME françaises**, construit sur un socle
 financier tracé (ledger REA immuable) que l'on étend par des chambres vendues
 séparément — la première étant un **WMS** (fiche cible v0.2, [[Charte]] §2).

## 2. Problème et gain

| Problème | Gain |
|---|---|
| ERP lourd : licences par utilisateur, serveur Windows, SQL Server, batch, personnalisation recompilée à chaque MA | Un socle événementiel en conteneurs, chaque écriture prouvable |
| Traçabilité parcoureuse (tableurs, comptes-rendus) | Chaque écriture prouvable, chaque exception tracée |
| Coût d'exploitation croissant avec la taille | Parité fonctionnelle, supériorité traçabilité, coût inférieur |

## 3. Job-Fonction-Pain (canvas)

| Job | Fonction | Pain empêché | Pain réduit par XoHive |
|---|---|---|---|
| Le DAF / comptable unique | Piloter la comptabilité générale, la TVA, la clôture | Saisies papier, retours cabinet, rapprochements manuels | Mécanique, temps de clôture |
| Le dirigeant (10–250) | Voir sa trésorerie et son résultat sans équipe lourde | Attendre le cabinet, relire, estimer | Lecture temps réel, suivi des chambres |
| Le gestionnaire / commercial | Devis, pipeline, facturation | Afinages en tableurs | CRM léger, workflow de vente |
| Le chef d'entrepôt | Stock, lots, réception | Excel de sécurité | Fiche cible, locale de stock, lots |

## 4. L'offre en v0 (socle)

- Comptabilité générale, TVA, clôture, facturation, achats, stocks.
- Moteur de documents : séquences sans trou, machine à états, chaîne de hachage.
- Traducteur de pièces comptables → écritures équilibrées.
- Projections de lecture + moteur d'édition PDF.
- Référentiels V1 : article, unités, tiers enrichi (13 106 comptes, 448 journaux, jeu de tiers
  168) + import X3 idempotent.
- **Machine à états et séquences sans trou** pour les documents (sortie : flux traversé
  brouillon → PDF → écriture équilibrée → chaîne de hachage, sans intervention manuelle).

## 5. Différenciation (vs concurrents §4)

| Critère | XoHive | Sage X3 / Cegid | Agicap / Pennylane |
|---|---|---|---|
| Comptabilité générale | ✅ socle V0 | ✅ | ❌ |
| Traçabilité immuable | ✅ (invariants I1–I9) | variable | ❌ |
| Coût d'exploitation | inférieur (conteneurs, no SQL Server) | élevé | bas |
| Multi-dossier | V4 | Oui | non |
| Multi-devises | V4 | oui | non |

## 6. 3 priorités

1. **Socle V0 livré** : moteur de documents, traducteur, projections, PDF ([[Charte]] §3.1).
2. **Référentiels V1** : 13 106 comptes, 448 journaux, tiers enrichi, import X3
   ([[Charte]] §3.2).
3. **Démonstration défendable** : vente complète (devis → commande → BL → facture → avoir)
   sans saisie d'écriture ([[Charte]] §3.3).

## 7. 3 hypothèses à tester

| H | Contenu | Seuil de falsification |
|---|---|---|
| H-01 | PME en direct (et non cabinet) | 10 entretiens (5 PME / 5 cabinets) |
| H-02 | Prix 250–450 €/mois pour 5 utilisateurs | Validation fondateur + devis |
| H-04 | FR d'abord, multi-lang v4 | carte produit post-V3 |

## 8. 3 axes de validation

1. Démo défendable sur jeu de données de référence, sans accès DB ([[Charte]] §3.3).
2. Campagne de 10 entretiens avec verbatims ([[Protocole entretiens]]).
3. Test automatique complet le flux document → écriture → hachage ([[Charte]] §3.1).
