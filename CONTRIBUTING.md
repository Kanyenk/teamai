# CONTRIBUTING.md — Règles du projet

## Convention de branches

| Type | Modèle | Exemple |
|---|---|---|
| Nouvelle fonctionnalité | `feature/<ticket>-<description>` | `feature/001-add-authentication` |
| Correction de bug | `fix/<ticket>-<description>` | `fix/042-login-timeout` |
| Documentation | `docs/<description>` | `docs/update-api-spec` |
| Déploiement | `deploy/<description>` | `deploy/configure-docker` |
| Révisions | `chore/<description>` | `chore/cleanup-tests` |

### Règles

- Les branches sont créées depuis `main`.
- Les noms de branches sont en `kebab-case`.
- Aucune branche `master` ou `trunk` — seule `main` est utilisée.

## Convention de commits

| Préfixe | Usage | Exemple |
|---|---|---|
| `feat:` | Nouvelle fonctionnalité | `feat: add authentication` |
| `fix:` | Correction de bug | `fix: 401 on /health` |
| `docs:` | Modification de documentation | `docs: update API.md` |
| `style:` | Formatage, sans impact logique | `style: fix indentation` |
| `refactor:` | Changement sans nouvelle fonctionnalité | `refactor: extract validator` |
| `test:` | Ajout ou modification de tests | `test: cover auth 401` |
| `chore:` | Maintenance, tooling | `chore: update deps` |
| `perf:` | Amélioration de performance | `perf: optimize query` |

### Règles

- Une ligne de commit maximum.
- `scope` optionnel entre `:` et le message.
- Le message est en `lowercase` (sauf acronymes).
- Ne pas finir par un point ou une ponctuation.

### Exemples

```bash
git commit -m "feat: add token authentication"
git commit -m "fix: 401 on /health without auth"
git commit -m "docs: update API and RUNBOOK"
```

## Obligation de lancer les tests

Avant tout `git push`, tous les tests doivent passer :

```bash
# Tous les tests (90)
python3 -m unittest discover -s tests -v

# Avec l'option "error" sur les DeprecationWarning
python3 -W error::DeprecationWarning -m unittest discover -s tests -v
```

### Règle stricte

| Condition | Action |
|---|---|
| 1 test échoue | Ne pas pusher, corriger d'abord |
| 1 DeprecationWarning | Ne pas pusher, corriger d'abord |
| 90/90 tests OK | Pousser la branche |

## Mise à jour de la documentation

Si l'API change, la documentation doit être mise à jour en même temps :

| Élément modifié | Fichier à mettre à jour |
|---|---|
| Nouveau endpoint | `API.md`, `docs/openapi.yaml` |
| Changement de schéma | `API.md`, `ARCHITECTURE.md`, `docs/openapi.yaml` |
| Nouveau code de statut | `API.md`, `ARCHITECTURE.md`, `RUNBOOK.md` |
| Nouveau token/démarrage | `README.md`, `RUNBOOK.md`, `API.md` |

### Check-list avant commit

- [ ] `python3 -m unittest discover -s tests -v` → 90/90 OK
- [ ] `python3 -W error::DeprecationWarning -m unittest discover -s tests -v` → OK
- [ ] `git add <fichiers>`
- [ ] `git commit -m "type: message"`
- [ ] `git push origin <branche>`
