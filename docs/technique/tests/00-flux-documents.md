---
title: "00 — Jeux de tests pour le moteur de documents"
date: 2026-11-02
type: "technique"
tags: [xohive, technique, tests, moteur, documents]
source: "[[Charte]]; [[01-machine-documents]]"
---

# Jeux de tests correspondants au moteur de documents (Socle technique V0)

Ce dossier contient les jeux de tests pour vérifier le flux document →
écriture → hachage. Chaque jeu est indépendant et peut être exécuté seul.

## Structure du dossier

| Fichier | Auteur | Rôle |
|---|---|---|
| `tests/flux-documents.md` | TeamAI | Jeu de test du flux complet document → écriture → hachage |

## Règles de test

- Chaque jeu est autonome : il n'utilise que des données fictives et ne
  représente aucune entreprise réelle.
- La vérification est automatique : une assertion de base est faite à la fin
  de chaque étape.
- Le flux est testé afin que le moteur produise des résultats attendus (une
  organisation, une transaction, un hachage) sans intervention humaine.

## 1. Flux document → écriture → hachage

### Données

| Champ | Valeur |
|---|---|
| org_id | 1 |
| type_id | facture |
| num | 2025-001 |
| date_creation | 2025-11-25 |
| date_echeance | 2026-01-25 |
| date_echeance_payee | 2025-12-26 |
| montant_ttc | 2500,00 |
| montant_ht | 2083,33 |
| tva | 10,00 |

### Déroulement

1. Le document est créé en `brouillon`.
2. Une fois le contenu validé, il est envoyé à son destinataire.
3. L'état est mis à jour pour `brouillon_pdf`.
4. Une fois l'PDF généré, l'état est mis à jour pour `envoyé`.
5. Le document est reçu et l'état est mis à jour pour `en_cours`.
6. Le document est validé et l'état est mis à jour pour `exécuté`.
7. L'écriture comptable est enregistrée et l'état est mis à jour pour `écrit`.
8. Une fois l'écriture vérifiée, l'état est mis à jour pour `fermé`.

### Vérification

Le flux est vérifié de la manière suivante :

1. Une organisation est créée et enregistrée dans la base.
2. Un document est créé avec les valeurs de la liste.
3. Le document est ajouté à la base de données.
4. Le flux est exécuté pour vérifier les étapes précédentes.
5. Une fois le flux terminé, la base est vérifiée.

### Résultats

| Résultat | Valeur |
|---|---|
| Entreprise fictive | `LACHAUX` (appelé `LACHAUX` en tant que pseudonyme) |
| Nature de l'entreprise | PME française de 10-250 salariés |
| Numéro de l'entreprise | 100-0123456 |
| Date | 2025-11-25 |
| Montant TTC | 2500,00 |
| Montant HT | 2083,33 |
| TVA | 10,00 |
| Indicateurs | Total de 10 articles (tilage) |

### Signification

- La création du document est faite avec succès.
- Le flux document → écriture → hachage est correctement réalisé.
- L'état du document est `écrit`.
- Le document est maintenant en lecture seule.
- La chaîne de hachage est immuable.
