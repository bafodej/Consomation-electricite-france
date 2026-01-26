# Consommation Électricité France - Analyse et Prédiction ML

Application complète d'analyse et prédiction de la consommation électrique française basée sur les données temps réel de RTE (Réseau de Transport d'Électricité).

## Aperçu

Pipeline data science et MLOps end-to-end :
- Collecte de données via API RTE éCO2mix
- Base de données PostgreSQL avec conformité RGPD
- API REST pour exposition des données
- Dashboard interactif de visualisation
- Modèles ML de prédiction de consommation
- Tests automatisés et CI/CD
- Conteneurisation Docker

**Données** : 500+ enregistrements horaires de consommation électrique française

**Performance modèle** : MAE 3200 MW, R² 0.82

---

## Fonctionnalités

### API REST (FastAPI)
- Health check et statistiques
- Exposition des données de consommation
- Logging structuré JSON
- Documentation OpenAPI/Swagger

### Dashboard interactif (Streamlit)
- Visualisation temps réel
- Graphiques interactifs (Plotly)
- Statistiques clés (moyenne, pic, creux)
- Auto-refresh optionnel

### Machine Learning
- Benchmarking de 8 modèles comparés
- Tracking avec MLflow
- Cross-validation 5-fold
- Visualisations des performances

### DevOps
- Tests automatisés (pytest, couverture 73%)
- CI/CD GitHub Actions
- Scan sécurité (Bandit, Safety)
- Docker + docker-compose

---

## Architecture

```
├── api/                    # API FastAPI
├── data/                   # Données CSV RTE
├── database/               # SQLite
├── front/                  # Dashboard Streamlit
├── ml/                     # Machine Learning
│   ├── train_model.py
│   ├── benchmark_models.ipynb
│   └── models/
├── src/                    # Scripts utilitaires
├── tests/                  # Tests automatisés
├── .github/workflows/      # CI/CD
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Technologies

- **Backend** : FastAPI, SQLAlchemy, SQLite
- **Frontend** : Streamlit, Plotly
- **ML** : scikit-learn, XGBoost, MLflow
- **Data** : Pandas, Numpy
- **DevOps** : pytest, Docker, GitHub Actions

---

## Installation

### Prérequis
- Python 3.10+
- Git
- (Optionnel) Docker

### Installation locale

```bash
git clone https://github.com/bafodej/Consomation-electricite-france.git
cd Consomation-electricite-france

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Avec Docker

```bash
docker-compose up -d

# Accès services :
# API: http://localhost:8000
# Dashboard: http://localhost:8501
# MLflow: http://localhost:5000
```

---

## Utilisation

### 1. Collecter les données

```bash
python src/rte_consommation.py
```

### 2. Lancer l'API

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Documentation API : http://localhost:8000/docs

### 3. Lancer le dashboard

```bash
streamlit run front/app.py --server.port 8501
```

Dashboard : http://localhost:8501

### 4. Entraîner le modèle

```bash
python ml/train_model.py
```

Visualiser MLflow :
```bash
mlflow ui
```
MLflow UI : http://localhost:5000

### 5. Benchmarking modèles

```bash
jupyter lab ml/benchmark_models.ipynb
```

---

## Tests

```bash
# Tous les tests
pytest tests/ -v

# Avec couverture
pytest tests/ --cov=api --cov=src --cov-report=html

# Tests spécifiques
pytest tests/test_api.py -v
pytest tests/test_model.py -v
```

---

## CI/CD

Pipeline GitHub Actions automatique sur chaque push :
1. Tests multi-versions Python (3.10, 3.11, 3.12)
2. Qualité code (Black, isort, flake8)
3. Validation modèles ML
4. Scan sécurité (Bandit, Safety)

---

## Documentation

- **Veille technologique** : `docs/VEILLE_TECHNOLOGIQUE.md`
- **Troubleshooting** : `docs/TROUBLESHOOTING.md`
- **API** : http://localhost:8000/docs (OpenAPI/Swagger)

---

## Métriques

### Performance modèle
- **MAE** : 3,200 MW
- **RMSE** : 4,100 MW
- **R²** : 0.82
- **MAPE** : 7.1%

### Qualité code
- **Couverture tests** : 73%
- **Tests passants** : 6/7
- **Vulnérabilités** : 0

### Données
- **Période** : 1-21 janvier 2026
- **Enregistrements** : 500 mesures horaires
- **Consommation moyenne** : 45,024 MW
- **Pic** : 60,447 MW
- **Creux** : 27,631 MW

---

## Auteur

**Bafodé Jaiteh**


---

## Liens utiles

- [API RTE éCO2mix](https://odre.opendatasoft.com/)
- [Documentation FastAPI](https://fastapi.tiangolo.com)
- [Documentation Streamlit](https://docs.streamlit.io)
- [Documentation MLflow](https://mlflow.org/docs)
