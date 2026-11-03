# Utilisation de l'image Python 3.12 slim
FROM python:3.12-slim

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TEAMAI_DB_PATH=/app/data/teamai.db
ENV TEAMAI_TOKENS=""

# Répertoire de travail
WORKDIR /app

# Copie des fichiers nécessaires
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Copie du code source
COPY engine ./engine
COPY tests ./tests

# Création du répertoire de données
RUN mkdir -p /app/data

# Exposition du port 8080
EXPOSE 8080

# Commande de démarrage
CMD ["python3", "-m", "engine.http", "--host", "0.0.0.0", "--port", "8080"]
