#!/bin/bash
set -e

echo "=== Initialisation des données ==="
python src/create_dataset.py
python src/load_jours_feries.py
python src/scrape_prix_electricite.py
python src/etl_fusion_donnees.py

echo "=== Démarrage de l'API ==="
exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
