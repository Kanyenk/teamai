---
title: "01 — Validation de la fiche-cadre XoHive"
date: 2026-11-02
type: "direction"
tags: [xohive, validation, charte, 7-éléments]
source: "[[Charte]]"
---

# Validation — XoHive (V0 canvas / marché)

*Résultat de l'agent `validation`. Aligné sur la définition de « terminé » de la charte :
**7 éléments** — événement, invariant, test de cycle, route API, écran, édition, ligne de
couverture.

## 1. Décision de conformité

| Critère | Résultat | Note |
|---|---|---|
| a) Aucun chiffre inventé | ❌ **Échec partiel** | L'angled (docs/direction/01-marche.md) cite des sources ; certains seuils (ex. budget 50–300 €/mois) viennent de docs tiers et restent indicative. |
| b) Cible cohérente (PME 10–250) | ✅ OK | Charte §2 maintenue. |
| c) Hypothèses identifiées, non tranchées | ✅ OK | H-01, H-02, H-04 listées comme à tester. |
| d) Pas de duplication de données | ✅ OK | Socle unique ; pas de chambre dupliquant un objet du socle. |

## 2. Points-correctifs identifiés

1. **Biblio indicative** : les fourchettes de budget (50–300 €/mois) et le classement
   (Agicap 399 €/mois…) viennent de docs tiers. À consigner comme *hypothèses hors
   production* jusqu'à validation fondateur.
2. **Jaune** : le Sellsy (trésorerie) et Qonto figurent dans un flux de trésorerie ;
   ne pas les confondre avec un ERP. À nettoyer dans la revue concours si conservé.
3. **Avertissement** : la comparaison à l'encontre de Sage X3 / Cegid est indicative et
   fondée sur l'état de la V0, non sur une production.

## 3. Engagé par le fondateur

Aucun engagement commercial, aucun chiffre de vente, aucun taux de satisfaction sans
source. Les hypostrophes restent des hypothèses jusqu'à validation.
