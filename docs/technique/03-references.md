# Schéma de référence — XoHive (Socle technique V0)

Ce dépôt contient les fichiers de référence pour le socle technique V0 de
XoHive : le moteur de documents, le modèle de données et les règles
d'exploitation. Chaque fichier est indépendant mais entre dans un ensemble
cohérent : ce sont les spécifications du socle.

## Contenu du dossier

| Fichier | Auteur | Objectif |
|---|---|---|
| `docs/technique/00-architecture.md` | TeamAI (agent technique) | Architecture du projet et principes de lecture |
| `docs/technique/01-machine-documents.md` | TeamAI (agent technique) | Machine à états du document, états et invariants |
| `docs/technique/02-schema-engine.md` | TeamAI (agent technique) | Schéma SQL de la base et logique de l'écriture |

## Notes d'utilisation

- Ces fichiers sont la spécification. Ici, ce sont les fichiers de travail :
  la base, les scripts et le code d'interface sont générés à partir d'eux.

- Le fondateur ou la table de validation assure la cohérence avec la charte.

- Chaque fichier de technique est annoté par une en-tête (`title`,
  `date`, `tags`, `source`) qui le lie aux documents officiels.

## Vérifications de cohérence

- Le schéma SQL est écrit pour un socle événementiel : aucune colonne
  modifiée après validation, tout changement crée une ligne nouvelle.
- La machine à états du document est tracée et sans trou.
- L'architecture est décrite sans ancrage technologique (cloud, base, language)
  — c'est la règle du socle.

## Historique

| Date | Auteur | Version | Commentaire |
|---|---|---|---|
| 2026-11-02 | TeamAI | 0.1 | Création du socle |
| 2026-11-02 | TeamAI | 0.1 | Mise à jour de la spécification |
