# RUNBOOK.md — Instructions opérationnelles

## Démarrer le service en arrière-plan avec nohup

```bash
# Prérequis : créer le dossier data et la base
mkdir -p data
python3 -c "from engine.repository import DocumentRepository; DocumentRepository('data/teamai.db')"

# Démarrer en arrière-plan (nohup)
TEAMAI_TOKENS="tok_123,dev-token" \
  nohup python3 -m engine.http \
    --host 0.0.0.0 \
    --port 8080 \
    --db data/teamai.db \
    > data/server.log 2>&1 &

# Enregistrer le PID pour un arrêt propre
echo $! > data/server.pid
```

### Explication

| Élément | Valeur |
|---|---|
| `TEAMAI_TOKENS` | Tokens autorisés (séparés par `,`), obligatoire |
| `python3 -m engine.http` | Point d'entrée du serveur |
| `--host 0.0.0.0` | Écoute sur toutes les interfaces |
| `--port 8080` | Port d'écoute |
| `--db data/teamai.db` | Chemin vers la base SQLite |
| `> data/server.log 2>&1` | Redirection de stdout et stderr vers un fichier de logs |
| `nohup` | Garde le processus en vie après déconnexion |
| `&` | Lance en arrière-plan |

### Vérifier que le processus tourne

```bash
ps aux | grep "engine.http" | grep -v grep
# hermes   12916  0.2  0.2  ...  python3 -m engine.http --host 0.0.0.0 --port 8080
```

## Arrêt propre

```bash
# Récupérer le PID
PID=$(cat data/server.pid)

# Envoyer le signal SIGTERM (gestioné par serveur)
kill -TERM $PID

# Attendre la fin du processus
wait $PID

# Vérifier
ps aux | grep "engine.http" | grep -v grep  # (ne doit rien afficher)
```

### Si le processus ne répond pas

```bash
# Forcer l'arrêt (SIGKILL)
kill -9 $PID
```

## Où trouver les logs

| Fichier | Contenu |
|---|---|
| `data/server.log` | Sortie du serveur (stdout + stderr) — messages d'erreur, état |
| `data/teamai.db` | Base de données SQLite (fichier binaire) |
| `data/server.pid` | PID du processus (écrit au démarrage) |

```bash
# Lire les 10 dernières lignes
tail -n 10 data/server.log

# Suivre les logs en temps réel
tail -f data/server.log
```

## Vérifications post-démarrage

### 1. Santé du service

```bash
curl -s http://localhost:8080/health
# Réponse attendue : {"status": "ok"}
```

### 2. Authentification

```bash
# Sans token → 401
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/documents
# Réponse attendue : 401

# Avec token valide → 201
curl -s -X POST http://localhost:8080/documents \
  -H "Authorization: Bearer tok_123" \
  -H "Content-Type: application/json" \
  -d '{"doc_type": "FACT", "numero_serie": 1, "org_id": 1}'

# Avec token invalide → 401
curl -s -X POST http://localhost:8080/documents \
  -H "Authorization: Bearer invalid" \
  -H "Content-Type: application/json" \
  -d '{"doc_type": "FACT", "numero_serie": 1, "org_id": 1}'
# Réponse attendue : 401
```

## Rotation du token API

1. **Générer un nouveau token** (side server ou variable d'environnement)
2. **Ajouter le nouveau token** à la liste `TEAMAI_TOKENS` :
   ```bash
   TEAMAI_TOKENS="tok_123,new-token-2026" nohup python3 -m engine.http --host 0.0.0.0 --port 8080 --db data/teamai.db
   ```
3. **Vérifier** que le serveur redémarre proprement :
   ```bash
   tail -n 5 data/server.log
   ```
4. **Tester** avec le nouveau token :
   ```bash
   curl -s -H "Authorization: Bearer new-token-2026" http://localhost:8080/health
   ```

## Sauvegarde de la base SQLite

```bash
# Sauvegarde simple (copie)
cp data/teamai.db data/teamai.db.backup

# Sauvegarde compressée
tar -czf data/teamai.db.backup.tar.gz data/teamai.db

# Restauration
cp data/teamai.db.backup data/teamai.db
```

### Sauvegarde automatique (cron)

```bash
# Exemple : sauvegarde quotidienne à 02:00
0 2 * * * cp /opt/projects/teamai/data/teamai.db /opt/projects/teamai/data/backup/teamai_$(date +\%Y\%m\%d).db
```
