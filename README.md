# Consommation Électricité France - Analyse et Prédiction ML

Application complète d'analyse et prédiction de la consommation électrique française basée sur les données temps réel de RTE (Réseau de Transport d'Électricité).

## Aperçu

Pipeline data science et MLOps end-to-end :
- Collecte 3 types sources : API + Fichier texte + Web scrapping
- Pipeline ETL de fusion et enrichissement
- Base de données PostgreSQL avec conformité RGPD
- API REST pour exposition des données
- Dashboard interactif de visualisation
- Modèles ML de prédiction de consommation
- Monitoring avec Prometheus et Grafana
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
- Benchmarking de 3 algorithmes (Linear, GradientBoosting, RandomForest)
- Modèle RandomForest sélectionné
- Tracking avec MLflow
- Cross-validation 5-fold
- Visualisations des performances

### DevOps
- Tests automatisés (pytest, couverture 73%)
- CI/CD GitHub Actions
- Scan sécurité (Bandit, Safety)
- Docker + docker-compose

### Monitoring
- Prometheus : collecte métriques temps réel
- Grafana : dashboards de visualisation
- Métriques API : requêtes, latence, erreurs
- Alerting configurable

---

## Architecture

```
├── api/                    # API FastAPI
├── data/                   # Données CSV (3 sources)
├── database/               # Bases de données
│   ├── rte_consommation.db     # SQLite
│   └── init_postgres.sql       # Schema PostgreSQL
├── front/                  # Dashboard Streamlit
├── ml/                     # Machine Learning
│   ├── train_model.py
│   ├── train_model.ipynb
│   ├── benchmark_models.ipynb
│   └── models/
├── monitoring/             # Prometheus & Grafana
│   ├── prometheus.yml          # Config Prometheus
│   ├── grafana/                # Dashboards Grafana
│   └── README.md
├── notebooks/              # Notebooks d'exploration
│   └── etl_exploration.ipynb
├── src/                    # Scripts collecte et ETL
│   ├── create_dataset.py       # API RTE
│   ├── load_jours_feries.py    # Fichier CSV
│   ├── scrape_prix_electricite.py  # Web scrapping
│   ├── etl_fusion_donnees.py   # Pipeline ETL
│   └── import_to_postgres.py   # Migration SQLite -> PostgreSQL
├── tests/                  # Tests automatisés
├── .github/workflows/      # CI/CD
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Base de données

Le projet supporte **deux types de bases de données** avec basculement automatique:

### SQLite (par défaut)
- Base de données locale légère
- Fichier unique : `database/rte_consommation.db`
- Idéal pour développement et tests
- Aucune installation requise

### PostgreSQL (production)
- Base de données relationnelle robuste
- Conformité RGPD avec modélisation MCD/MLD
- Support multi-utilisateurs et transactions
- Déployable via Docker

### Configuration

**Pour utiliser SQLite (par défaut):**
```bash
# Aucune config nécessaire, utilisé automatiquement
python src/create_dataset.py
```

**Pour utiliser PostgreSQL:**

1. Créer fichier `.env`:
```bash
DATABASE_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=rte_consommation
POSTGRES_USER=rte_user
POSTGRES_PASSWORD=rte_secure_password
```

2. Lancer PostgreSQL avec Docker:
```bash
docker-compose up -d postgres
```

3. Migrer les données SQLite vers PostgreSQL:
```bash
python src/import_to_postgres.py
```

### Tables disponibles

- **consommation** : Données de consommation électrique (API RTE)
- **calendrier_feries** : Jours fériés et vacances (CSV)
- **prix_spot_electricite** : Prix spot horaires (Web scrapping)
- **conso_enrichi_3sources** : Données fusionnées enrichies (ETL)
- **meteo** : Données météorologiques (optionnel)
- **prevision** : Prédictions du modèle ML

---

## Monitoring

Le projet inclut un système de monitoring complet avec **Prometheus** et **Grafana**.

### Prometheus
- Collecte automatique des métriques API
- Scraping toutes les 15 secondes
- Retention 15 jours
- Interface web: http://localhost:9090

### Grafana
- Dashboard pré-configuré "RTE API - Monitoring"
- Visualisations temps réel
- Credentials: admin/admin
- Interface web: http://localhost:3000

### Métriques disponibles

**API Performance:**
- `api_requests_total` : Nombre total de requêtes par endpoint/status
- `api_request_duration_seconds` : Latence des requêtes (histogramme)
- `api_requests_in_progress` : Requêtes en cours de traitement
- `api_errors_total` : Nombre d'erreurs par type

**Base de données:**
- `db_consommation_records_total` : Nombre d'enregistrements en base

### Dashboard Grafana

Le dashboard inclut:
1. Taux de requêtes par minute
2. Requêtes en cours (temps réel)
3. Nombre d'enregistrements en base
4. Latence p95 par endpoint
5. Taux d'erreurs
6. Distribution par endpoint
7. Status HTTP (200, 400, 500...)

### Démarrage

```bash
# Lancer tous les services incluant monitoring
docker-compose up -d

# Accès aux interfaces:
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000
# - Métriques API: http://localhost:8000/metrics
```

### Exemples de requêtes PromQL

```promql
# Taux de requêtes par seconde
rate(api_requests_total[1m])

# Latence p95
histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m]))

# Taux d'erreurs
sum(rate(api_errors_total[5m]))
```

Documentation complète: `monitoring/README.md`

---

## Technologies

- **Backend** : FastAPI, SQLAlchemy
- **Base de données** : SQLite, PostgreSQL (dual support)
- **Frontend** : Streamlit, Plotly
- **ML** : scikit-learn, XGBoost, MLflow
- **Data** : Pandas, Numpy
- **Monitoring** : Prometheus, Grafana
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
# Lancer tous les services
docker-compose up -d

# Services disponibles:
# PostgreSQL: localhost:5432
# API: http://localhost:8000
# Dashboard: http://localhost:8501
# MLflow: http://localhost:5000
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000
```

---

## Utilisation

### 1. Collecter les données (3 types sources)

**Type 1 - API : Consommation électrique RTE**
```bash
python src/create_dataset.py
```

**Type 2 - Fichier texte : Jours fériés français**
```bash
python src/load_jours_feries.py
```

**Type 3 - Web scrapping : Prix spot électricité**
```bash
python src/scrape_prix_electricite.py
```

**Pipeline ETL - Fusion 3 sources:**
```bash
python src/etl_fusion_donnees.py
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

### 5. Benchmarking algorithmes (optionnel)

```bash
jupyter lab ml/benchmark_models.ipynb
```

Compare 3 algorithmes pour justifier le choix du RandomForest.

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
- **Monitoring** : `monitoring/README.md`
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
