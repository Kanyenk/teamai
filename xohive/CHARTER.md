# XoHive — Module Documents & Comptabilité

## Positionnement
Ce dépôt est le module « Documents & Comptabilité » de la plateforme XoHive.
Il ne constitue pas XoHive dans son ensemble.

## Périmètre actuel
- Moteur de documents (création, lecture, liste, transition)
- Validation métier (types, soldes, devises, transitions)
- Persistance SQLite
- API HTTP sécurisée par token Bearer
- Documentation OpenAPI
- Déploiement Docker

## Hors périmètre (autres modules XoHive)
- CRM
- Ventes / Facturation
- Achats
- Stocks / WMS
- Projets
- RH

## Prochain module prioritaire
CRM minimal (contacts, entreprises, opportunités, pipeline, activités)

## Prérequis avant nouveau module
Définir le modèle commun :
Organization, User, Role, Permission, Party, Document, Workflow, AuditEvent, LedgerEntry

## Règles
- Toute nouvelle fonctionnalité doit mettre à jour README, ARCHITECTURE, API.
- Les tests doivent passer avant tout push.
- Le token API reste dans .env.local, jamais versionné.
