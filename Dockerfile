# Dockerfile pour l'API RTE Consommation
# RNCP C19: Déploiement continu de l'application

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
COPY ml/models/ ./ml/models/

# Créer les répertoires nécessaires
RUN mkdir -p logs

# Exposer le port de l'API
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/')" || exit 1

# Commande de démarrage
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
