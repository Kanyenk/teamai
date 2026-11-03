# TROUBLESHOOTING.md — Dépannage

## 1. curl retourne 000

**Symptôme :** `curl -s http://localhost:8080/health` → `curl: (28) Connection timed out` ou `000`

**Causes possibles :**

| Cause | Vérification | Correction |
|---|---|---|
| Le serveur n'est pas démarré | `ps aux \| grep engine.http` | Démarrer avec `nohup python3 -m engine.http --host 0.0.0.0 --port 8080` |
| Le port n'est pas écouté | `ss -ltnp \| grep 8080` | Vérifier le port ou utiliser `--port` |
| Le serveur a planté | `tail -n 20 data/server.log` | Lire les erreurs |
| Le firewall bloque | `sudo ufw status` | Configurer le firewall |

**Commandes de diagnostic :**

```bash
# Vérifier si le processus tourne
ps aux | grep "engine.http" | grep -v grep

# Vérifier si le port est ouvert
ss -ltnp | grep 8080
# (ou) netstat -tlnp | grep 8080

# Vérifier les logs
tail -n 20 data/server.log

# Tenter une requête avec verbose
curl -v http://localhost:8080/health
```

## 2. 401 inattendu

**Symptôme :** `curl -s -H "Authorization: Bearer tok_123" http://localhost:8080/documents` → `401`

**Causes possibles :**

| Cause | Vérification | Correction |
|---|---|---|
| Le token n'est pas dans `TEAMAI_TOKENS` | Voir `printenv TEAMAI_TOKENS` | Ajouter le token à la liste |
| Le token a une espace ou une virgule | `TEAMAI_TOKENS="tok_123" echo $TEAMAI_TOKENS` | Vérifier le format |
| Le header n'est pas bien formatté | `curl -v` | Utiliser `Authorization: Bearer <token>` |

**Correction :**

```bash
# Exemple : avec deux tokens
TEAMAI_TOKENS="tok_123,dev-token" python3 -m engine.http --host 0.0.0.0 --port 8080
```

## 3. 500 — Erreur interne

**Symptôme :** `curl -s -X POST http://localhost:8080/documents` → `500`

**Actions :**

```bash
# Lire les logs
tail -n 30 data/server.log

# Rechercher l'erreur
grep -E "(ERROR|Exception|Error)" data/server.log
```

**Erreurs communes et corrections :**

| Code d'erreur | Message | Correction |
|---|---|---|
| `400` | `type de document inconnu` | `doc_type` doit être dans `FACT, BC, BL, NC, RS, CHQ` |
| `400` | `numero_serie invalide` | `numero_serie` doit être un entier > 0 |
| `400` | `org_id invalide` | `org_id` doit être un entier > 0 |
| `400` | `currency invalide` | Devise de 3 caractères (ex: `EUR`) |
| `400` | `balance négative` | `balance` ≥ 0 |
| `401` | `missing or invalid token` | Ajouter le token à `TEAMAI_TOKENS` |
| `404` | `document introuvable` | Vérifier l'`id` du document |

## 4. Port déjà utilisé

**Symptôme :** `OSError: [Errno 98] Address already in use`

**Diagnostic :**

```bash
# Qui utilise le port 8080 ?
ss -ltnp | grep 8080

# (ou)
sudo lsof -i :8080
```

**Correction :**

- Arrêter le processus qui utilise le port
- ou utiliser un autre port :
  ```bash
  python3 -m engine.http --host 0.0.0.0 --port 8081
  ```

## 5. Base de données corrompue

**Symptôme :** `sqlite3.OperationalError: database disk image is malformed`

**Procédure de récupération :**

```bash
# 1. Arrêter le serveur si démarré
kill -TERM $(cat data/server.pid) 2>/dev/null

# 2. Vérifier l'intégrité de la base
sqlite3 data/teamai.db "PRAGMA integrity_check;"
# (sqlite3 peut ne pas être installé : python3 -c "import sqlite3; sqlite3.connect('data/teamai.db')" )

# 3. Créer une nouvelle base (les données sont perdues)
rm -f data/teamai.db
python3 -c "from engine.repository import DocumentRepository; DocumentRepository('data/teamai.db')"

# 4. Démarrer le serveur
TEAMAI_TOKENS="tok_123" nohup python3 -m engine.http --host 0.0.0.0 --port 8080 --db data/teamai.db
```

### Sauvegardes

```bash
# Sauvegarde avant réparation
cp data/teamai.db data/teamai.db.backup.$(date +%Y%m%d)

# Restauration à partir de la sauvegarde
cp data/teamai.db.backup data/teamai.db
```
