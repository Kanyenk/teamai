# XoHive — Moteur de documents (Socle technique V0)

Moteur de documents événementiels pour le socle financier de XoHive.

## Principe

Chaque document (facture, bon de commande, bon de livraison, note de crédit,
reçu, pièce justificative) est modélisé comme une **machine à états** parcourue
sans trou, avec une **chaîne de hachage** immuable. Aucune transition n'est
autorisée sauf si elle respecte les invariants L1–L9.

Les documents ne sont pas sauvegardés en base brute : une écriture est
équilibrée, une chaîne de hachage est recalculée, et seule la vérité est enregistrée.

## États possibles

| État | Description |
|---|---|
| `brouillon` | Document en construction, modifié librement |
| `brouillon_pdf` | Brouillon, export PDF généré |
| `envoyé` | Document envoyé (email, réception) |
| `remis` | Document remis au tiers (BL, réception) |
| `en_cours` | En cours de traitement |
| `exécuté` | Document autorisé à être intégré |
| `écrit` | Écriture en base validée |
| `fermé` | Document archivé, en lecture seule |
| `annulé` | Annulation (crée une écriture inversée) |
| `supprimé` | Suppression logique, dans l'archive |

## Séquences sans trou

Une séquence est un chemin d'exécution strict. Un document ne peut passer d'un
état à un autre que par une transition autorisée.

Exemple pour une facture (en entrée) :

```
brouillon → brouillon_pdf → envoyé → en_cours → exécuté → écrit → fermé
```

Chaque transition doit être explicitement autorisée par la règle métier.

## Règles de sécurité (invariants L1–L9)

| Règle | Description |
|---|---|
| L1 | Aucune transition invalide : une machine à états contrôle le flux |
| L2 | Une chaîne de hachage est toujours recalculée après une écriture |
| L3 | Un document ne peut être édité en lecture seule (état `fermé`, `écrit`, `archivé`) |
| L4 | Une écriture équilibre nécessairement la base (débit = crédit) |
| L5 | Une clause de type de document est impérative (FF, BC, BL, NC, reçu) |
| L6 | Un document envoyé n'est pas modifiable sans signature |
| L7 | Un document en `brouillon_pdf` génère une référence PDF (hash) |
| L8 | Un document `exécuté` ne peut être modifié que par une annulation |
| L9 | Le moteur ne supprime jamais une écriture : il la marque annulée |

## Machine à états

L'état est une machine à états avec transitions pré-définies. Chaque document
nécessite un état et une règle de transition.

```
État initial : brouillon

Transitions autorisées :
- brouillon → brouillon_pdf (génération PDF)
- brouillon_pdf → envoyé (envoi)
- envoyé → en_cours (réception)
- en_cours → exécuté (validation)
- exécuté → écrit (enregistrement)
- écrit → fermé (archivage)
- écrire → annulé (annulation)
- annulé → écrit (rétablissement après correction)
- écrit → supprimé (suppression logique)
```

## Autres notes

- La séquence est tracée : chaque transition est journalisée avec l'acteur
  et la date.
- La chaîne de hachage est recalculée à chaque écriture.
- Le document est immuable une fois fermé.
- Le moteur ne suppose aucune base de données ou framework : c'est une interface
  pure, implémentable sur n'importe quel SOC.
