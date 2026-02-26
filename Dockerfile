# Dockerfile pour l'API RTE Consommation

FROM python:3.12-slim

LABEL maintainer="bafodej"
LABEL description="API de consommation électrique France RTE"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY api/ ./api/
COPY src/ ./src/
COPY database/ ./database/
COPY data/ ./data/
COPY ml/models/ ./ml/models/
COPY entrypoint.sh .

# Créer les répertoires nécessaires
RUN mkdir -p logs && chmod +x entrypoint.sh

# Exposer le port de l'API
EXPOSE 8000

# Commande de démarrage : initialise la DB puis lance l'API
CMD ["./entrypoint.sh"]
