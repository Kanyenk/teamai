---
title: "01 — Lectures et état de synthèse"
date: 2026-11-02
type: "direction"
tags: [xohive, lectures, synthèse, actions]
source: "[[Charte]]"
---

# Lectures — marche / canvas / validation

*Agent `orchestrator`. Synthèse des trois fichiers de direction.

## 1. Constat

La **cible est cohérente** (PME 10–250, finance 1–5, services / négoce technique /
industrie légère) et la **position est décelable** dans un marché dense : aucun concurrent
ne propose un socle comptable + traçabilité immuable + coût inférieur sur le mouillage
événementiel. Le vrai trou : la traçabilité *exécutable* sans SQL Server dédié, et la
descente technique facturée sans consultant.

## 2. Hypothèses en l'état

| H | État | Ce qui manque |
|---|---|---|
| H-01 | à tester | Campagne de 10 entretiens (5 PME / 5 cabinets) |
| H-02 | à tester | Validation fondateur + demande de devis |
| H-04 | à tester | Carte produit post-V3 |

## 3. Actions à entreprendre (suivants)

| # | Action | Agent | Jour C |
|---|---|---|---|
| A1 | Lancer la campagne de 10 entretiens (5 PME, 5 cabinets) | researcher | C+1 |
| A2 | Mettre en place la V0 technique (moteur doc, traducteur, flux + hash) | engineer | C+1 → C+5 |
| A3 | Préparer la démonstration défendable (données de référence, pas d'accès DB) | engineer | C+5 |
| A4 | Valider le prix H-02 auprès du fondateur | orchestrator | C+2 |
| A5 | Vérifier la couverture exécutable (test de cycle) | validation | C+3 |

## 4. Principe d'arrêt

Tout engagement commercial, toute décision de prix ou de segment doit passer par la
validation du fondateur (`outbox/pending/`). Aucun agent n'invente de chiffre ni de
témoignage.
