---
title: "01 — Scan de marché (XoHive)"
date: 2026-11-02
type: "direction"
tags: [xohive, marché, scan, 2026, recherche]
source: "[[Charte]]; Fortune Business Insights; Mordor Intelligence; Apogea (Apps Run The World)"
---

# Scan de marché — XoHive

*Agent `researcher`. Chiffres sources ; le reste = hypothèses à tester.*

## 1. Milieu global

| Indicateur | Valeur | Source |
|---|---|---|
| Marché SaaS mondial 2025 | 315,68 MD$ | Fortune Business Insights (fr) |
| Marché SaaS mondial 2026 | 375,57 MD$ | Fortune Business Insights (fr) |
| Marché ERP mondial 2025 | ≈ 146–148 MD$ | Akuiteo / Apps Run The World |
| Cloud ERP 2025 | 65,89 MD$ | Apogea (source Apps Run The World) |
| Marché ERP mondial 2026 | 78,15 MD$ → 133,3 MD$ (2030) | Mordor Intelligence (fr) |

Le marché est **en croissance +11 %/an** et le segment cloud est le plus démographé. C'est
ce qui rend réalisable la migration d'un socle comptable vers un SaaS tracé.

## 2. Cible — PME française 10–250 salariés

- Secteurs visés : **services, négoce technique, industrie légère**.
- Équipe finance **1–5 pers** : DAF ou dirigeant assisté d'un comptable.
- Système actuel : **Sage X3, Sage 100**, ou tableurs + cabinet comptable.
- Déclencheur : fin de version, coût des licences, personnalisation devenue intenable.
- Niveau technique : faible, utilisation sans formation lourde, sans consultant.
- Budget : **inférieur au coût économisé** (licences + serveur + intégrateur).

## 4. Concurrents directs (pour une PME 10–250)

| Outil | Cible | Seuil d'entrée | Nota |
|---|---|---|---|
| Sage X3 / Sage 100 | PME/ETI | licence serveur SQL | Lourd, coût de garde élevé |
| Cegid (Rex / XRP) | ETI / Grandes entreprises | Devis | Sur-développé pour 10–250 |
| Odoo | PME | Abonnement / open-source | Nécessite une chaîne de valeur |
| Agicap | Trésorerie PME 5–500 | 399 €/mois | Produit du trésorier, pas de compta |
| Fygr | Trésorerie PME 1–200 | 149 €/mois | Paiement pénal, pas de compta générale |
| Pennylane | Trésorerie + frais | 49 €/mois | Ne remplace pas la comptabilité |
| Qonto | Neo-banque + trés. | 9 €/mois | Pauvre en comptabilité |

→ **Aucun concurrent ne répond à l'offre cible dans sa globalité** : le socle
comptable + traçabilité *tracée* + coût d'exploitation inférieur, sur le socle
événementiel (pas SQL Server/Windows).

## 5. Positionnement et trou de marché

Positionnement en une ligne ([[Charte]] §1) : **parité fonctionnelle sur le socle,
supériorité sur la traçabilité, coût d'exploitation inférieur.**

Ce qui manque dans la bouche de concurrents : **une traçabilité exécutable qui ne
coûte pas un environnement SQL Server dédié**, et une descente technique facturée
sans consultant.

## 6. Hypothèses à tester

| H | Contenu | Seuil de falsification |
|---|---|---|
| H-01 | Segment d'attaque : PME en direct (et non cabinet) | Campagne de 10 entretiens (5 PME / 5 cabinets) |
| H-02 | Prix : 250–450 €/mois pour 5 utilisateurs | Validation fondateur + demande de devis |
| H-04 | Échelle des langues : FR d'abord, multi-lang v4 | Carte produit post-V3 |

**Sources:** Charte §1, §2, §3, §8, §9. Chiffres statistiques : Fortune Business
Insights, Mordor Intelligence, Apogea/Aapps Run The World (cf. tableau §1).
