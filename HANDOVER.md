# HANDOVER.md — Transfert de projet

> Document de transfert pour la reprise de l'équipe TeamAI. À lire par tout nouveau membre avant de toucher au code.

---

## 1. Liste des personnes/rôles

| Rôle | Personne | Mission principale |
|---|---|---|
| **Chef de projet / Product Owner** | `Kanyenk` (Github) | Validation de déploiement, priorisation des lots |
| **Développeur backend** | **Actuel développeur** | Maintien du service HTTP, ajout de fonctionnalités |
| **Développeur DevOps** | — | Maintenance des conteneurs, supervision `docker-compose` |
| **Chef de projet IA** | `Kanyenk` (Obsidian) | Conformité des agents IA, suivi des dossiers |

### Links GitHub

- **Dépôt officiel** : `https://github.com/Kanyenk/teamai`
- **Branche principale** : `main` (synchrone avec `origin/main`)
- **Branches de lot** (toutes fusionnées) : `http-api`, `ci-github-actions`, `business-validation`, `api-authentication`, `openapi-docs`, `docker-deployment`

---

## 2. Accès nécessaires

### GitHub (dépôt)

- **Lien** : `https://github.com/Kanyenk/teamai`
- **Authentification** : `https://github.com/Kanyenk/teamai.git` (via HTTPS + token)
- **Fonctionnement** :
  - Push sur `main` autorisé après merge (CI GitHub Actions vérifie les 90 tests)
  - Push sur les branches de lot autorisé pour les PRs
  - Aucun `force-push` sur `main`

### Serveur

- **Adresse** : `localhost` (démarrage local)
- **Port HTTP** : `8080` (TCP)
- **Base de données** : `data/teamai.db` (SQLite, WAL)
- **Logs** : `data/server.log`
- **PID** : `data/server.pid` (lors du démarrage nohup)
- **Docker** : `docker compose up -d --build` (port 8080:8080, volume `./data:/app/data`)

### Token API

| Variable | Description | Exemple |
|---|---|---|
| `TEAMAI_TOKENS` | Liste des tokens valides (séparés par `,`) | `tok_123,dev-token` |
| `TEAMAI_DB_PATH` | Chemin vers la base SQLite | `/app/data/teamai.db` |

> **Protection** : jamais exposer les tokens en clair. Garder les tokens côté serveur (variables d'environnement), pas dans le code ni les logs.

---

## 3. Points de vigilance

### Tokens à rotator

- Les tokens Bearer sont vérifiés par `engine/auth.py` (`TokenAuth.authenticate()`).
- `TEAMAI_TOKENS` est lu au démarrage : **ajouter un nouveau token sans redémarrer le service ne le rendra pas actif**.
- Rotation : générer un nouveau token, le rajouter à `TEAMAI_TOKENS`, redémarrer le service (`RUNBOOK.md` → Section 2).

### Base SQLite à sauvegarder

- Fichier : `data/teamai.db` (libellé WAL : `data/teamai.db-shm`, `data/teamai.db-wal`).
- Méthode : `cp data/teamai.db data/teamai.db.backup` (ou tar.gz).
- Fréquence recommandée : quotidienne (cron ou script manuel).
- Procédure de restauration : Section 6 du `RUNBOOK.md`.
- **Avertissement** : la base contient les documents créés. Ne pas modifier manuellement sans sauvegarde.

### Autres points de vigilance

| Point | Vérification | Action |
|---|---|---|
| Port 8080 occupé | `ss -ltnp \| grep 8080` | Arrêter le processus ou changer de port |
| Base corrompue | `sqlite3 data/teamai.db "PRAGMA integrity_check;"` | Récupération depuis sauvegarde (Section 5 TROUBLESHOOTING.md) |
| Logs pleins | `tail -f data/server.log` | Vérifier la taille, proposer rotation |
| Sequence 90/90 | `python3 -m unittest discover -s tests -v` | Toujours valider avant tout push |

---

## 4. Checklist de reprise (10 étapes)

> Pour un nouvel arrivant. À réaliser dans l'ordre.

### Prérequis système

1. **Vérifier l'accès au dépôt** : `git clone https://github.com/Kanyenk/teamai.git /opt/projects/teamai`
   - *Attendu* : dossier présent, arreste `origin/main` = `e56ebe4`
2. **Vérifier l'environnement Python** :
   ```bash
   python3 --version        # 3.12+
   python3 -c "import yaml" # PyYAML installé (requis pour les tests)
   ```
   - *Attendu* : version ≥ 3.12, `yaml` importable

### Dépannage rapide

3. **Vérifier que le serveur tourne** :
   ```bash
   curl -s http://localhost:8080/health
   # Réponse attendue : {"status": "ok"}
   ```
4. **Si le serveur ne répond pas** :
   - `ps aux | grep engine.http` → vérifier le PID
   - `tail -n 20 data/server.log` → lire les erreurs
   - `ss -ltnp | grep 8080` → vérifier le port

### Reprise du service

5. **Créer la base de données** (si absente) :
   ```bash
   mkdir -p data
   python3 -c "from engine.repository import DocumentRepository; DocumentRepository('data/teamai.db')"
   ```
6. **Démarrer le service en arrière-plan** :
   ```bash
   TEAMAI_TOKENS="tok_123,dev-token" nohup python3 -m engine.http --host 0.0.0.0 --port 8080 --db data/teamai.db > data/server.log 2>&1 &
   echo $! > data/server.pid
   ```
7. **Vérifier l'état du serveur** :
   ```bash
   curl -s http://localhost:8080/health
   curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/documents
   # 1ère réponse : {"status": "ok"} ; 2ème réponse : 401 (sans token)
   ```

### Maintien et documentation

8. **Lancer les tests** :
   ```bash
   python3 -m unittest discover -s tests -v     # 90/90 OK
   python3 -W error::DeprecationWarning -m unittest discover -s tests -v  # OK
   ```
9. **Consulter la documentation** :
   - `README.md` : présentation, stack, démarrage
   - `ARCHITECTURE.md` : modules, flux HTTP, architecture
   - `API.md` : endpoints, auth, exemples curl
   - `RUNBOOK.md` : démarrage, arrêt, logs, rotation, sauvegarde
   - `TROUBLESHOOTING.md` : dépannage
   - `CONTRIBUTING.md` : règles de branches, commits, tests
10. **Déployer avec Docker** (alternative au démarrage local) :
    ```bash
    TEAMAI_TOKENS="tok_123" docker compose up -d --build
    curl -s http://localhost:8080/health
    ```

---

## 5. Contacts et liens utiles

| Élément | Lien |
|---|---|
| Dépôt GitHub | `https://github.com/Kanyenk/teamai` |
| Branche principale | `main` (`origin/main` = `e56ebe4`) |
| Documentation interne | `ARCHITECTURE.md`, `API.md`, `RUNBOOK.md`, `TROUBLESHOOTING.md`, `CONTRIBUTING.md` |
| Contexte du projet | `docs/` (OpenAPI, technique, direction, contrat-agents) |
| Objet du projet | Engine de documents comptables (XoHive), service HTTP minimal, SQLite, authentification Bearer |
