---
title: "00 — Structure du projet — architecture"
date: 2026-11-02
type: "portefeuille"
tags: [xohive, architecture, socle, structure]
source: "[[Charte]]"
---

# Architecture du projet — XoHive (TeamAI)

Cet espace de travail est le dépôt de travail de l'équipe **TeamAI**, qui
construit le produit **XoHive** selon la charte et le cadre de gestion.

L'organisation en répertoires séparés reflète la séparation des préoccupations
de l'organisation :

| Répertoire | Rôle |
|---|---|
| `board/` | Backlog interactif, lectures et synthèses |
| `docs/` | Documentation stratégique, contrat, direction, techniques |
| `registry/` | Registre des agents disponibles |
| `agents/` | Agents individuels et leurs spécifications |
| `product/` | Livrables produits (v0, prototype, V1…) |
| `content/` | Documents de référence, notes et fichiers bruts |

> L'ordre alphabétique et la convention de nommage des dossiers sont des
> conventions de lecture, pas des contraintes de produit.

## Registre des agents

Le fichier `registry/agent_registry.yaml` liste les agents organisés par rôle.
Chaque agent est décrit par son rôle, son entrée et sa sortie.

Lire `registry/agent_registry.yaml` pour la liste complète des agents et leurs
responsabilités.

## Charte comme source unique

La charte XoHive reste la **source unique de la vérité** sur ce que produit la
table : tout nouvel agent lit la charte, et toute action épicée est validée
par le fondateur.

## Structure de travail

Le travail est organisé en cycles. Chaque cycle produit des livrables dans les
dossiers correspondants. Les livrables de compétence sont apportés par un
agent, puis validés par la table.

- Les fichiers de produit (V0, V1…) vont dans `product/`.
- Les notes brutes et les journaux vont dans `content/`.
- Les documents de référence vont dans `content/raw/` s'ils sont volumineux ou
  bruts.
