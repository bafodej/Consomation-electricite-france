# Monitoring avec Prometheus et Grafana

Ce dossier contient la configuration pour le monitoring du projet avec Prometheus et Grafana.

## Architecture

```
monitoring/
├── prometheus.yml                    # Configuration Prometheus
├── grafana/
│   └── provisioning/
│       ├── datasources/
│       │   └── prometheus.yml       # Datasource Prometheus auto-config
│       └── dashboards/
│           ├── dashboard.yml        # Provider de dashboards
│           └── rte-api-dashboard.json  # Dashboard pre-configure
└── README.md
```

## Services

### Prometheus (port 9090)
- Collecte metriques toutes les 15 secondes
- Scrape l'API sur `/metrics`
- Interface web: http://localhost:9090

### Grafana (port 3000)
- Visualisation des metriques
- Dashboard pre-configure
- Credentials par defaut: admin/admin
- Interface web: http://localhost:3000

## Metriques collectees

### Metriques API

**api_requests_total**
- Type: Counter
- Description: Nombre total de requetes HTTP
- Labels: method, endpoint, status
- Exemple: `api_requests_total{method="GET",endpoint="/conso",status="200"}`

**api_request_duration_seconds**
- Type: Histogram
- Description: Duree des requetes en secondes
- Labels: method, endpoint
- Buckets: 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10
- Exemple: `api_request_duration_seconds_sum{method="GET",endpoint="/stats"}`

**api_requests_in_progress**
- Type: Gauge
- Description: Nombre de requetes en cours de traitement
- Exemple: `api_requests_in_progress 3`

**db_consommation_records_total**
- Type: Gauge
- Description: Nombre total d'enregistrements en base de donnees
- Exemple: `db_consommation_records_total 500`

**api_errors_total**
- Type: Counter
- Description: Nombre total d'erreurs API
- Labels: endpoint, error_type
- Exemple: `api_errors_total{endpoint="/conso",error_type="HTTPException"}`

## Demarrage

### Avec Docker Compose

```bash
# Lancer tous les services incluant monitoring
docker-compose up -d

# Services disponibles:
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000
# - API metrics: http://localhost:8000/metrics
```

### Verification

```bash
# Verifier que Prometheus scrape l'API
curl http://localhost:9090/api/v1/targets

# Voir les metriques brutes de l'API
curl http://localhost:8000/metrics

# Tester une requete PromQL
curl -g 'http://localhost:9090/api/v1/query?query=api_requests_total'
```

## Utilisation Grafana

### Premiere connexion

1. Ouvrir http://localhost:3000
2. Login: `admin` / Password: `admin`
3. (Optionnel) Changer le mot de passe

### Dashboard pre-configure

Le dashboard "RTE API - Monitoring" est automatiquement charge et contient:

1. **Requetes par minute** - Graphique du taux de requetes
2. **Requetes en cours** - Nombre de requetes actuellement traitees
3. **Enregistrements en base** - Total des enregistrements
4. **Latence p95** - 95e percentile de latence
5. **Erreurs API** - Taux d'erreurs par endpoint
6. **Total par endpoint** - Repartition des requetes
7. **Status HTTP** - Repartition des codes de retour

### Creer des alertes

```yaml
# Exemple d'alerte Prometheus (a ajouter dans prometheus.yml)
groups:
  - name: api_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(api_errors_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Taux d'erreur eleve sur l'API"
          description: "Plus de 0.1 erreur/s pendant 2 minutes"
```

## Requetes PromQL utiles

### Taux de requetes

```promql
# Requetes par seconde sur 1 minute
rate(api_requests_total[1m])

# Requetes par endpoint
sum by(endpoint) (rate(api_requests_total[1m]))

# Requetes 4xx et 5xx
sum(rate(api_requests_total{status=~"4..|5.."}[5m]))
```

### Latence

```promql
# Latence moyenne
rate(api_request_duration_seconds_sum[5m]) / rate(api_request_duration_seconds_count[5m])

# p95 latence
histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m]))

# p99 latence
histogram_quantile(0.99, rate(api_request_duration_seconds_bucket[5m]))
```

### Disponibilite

```promql
# Taux de succes (non-5xx)
sum(rate(api_requests_total{status!~"5.."}[5m])) / sum(rate(api_requests_total[5m])) * 100

# Uptime (1 = up, 0 = down)
up{job="rte-api"}
```

## Arreter les services

```bash
# Arreter tous les services
docker-compose down

# Supprimer les donnees (attention: perte des metriques historiques)
docker-compose down -v
```

## Retention des donnees

Par defaut:
- **Prometheus**: 15 jours de retention
- **Grafana**: indefini (base SQLite interne)

Pour modifier la retention Prometheus, editer `docker-compose.yml`:

```yaml
prometheus:
  command:
    - '--storage.tsdb.retention.time=30d'  # 30 jours
```

## Export des metriques

```bash
# Export snapshot Prometheus
curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot

# Export dashboard Grafana (via API)
curl -X GET http://admin:admin@localhost:3000/api/dashboards/uid/rte-api-monitoring
```

## Troubleshooting

### Prometheus ne scrappe pas l'API

```bash
# Verifier que l'API expose /metrics
curl http://localhost:8000/metrics

# Verifier les targets dans Prometheus
curl http://localhost:9090/api/v1/targets

# Logs Prometheus
docker logs rte-prometheus
```

### Grafana n'affiche pas de donnees

1. Verifier que Prometheus collecte les metriques
2. Verifier la datasource dans Grafana: Configuration > Data Sources
3. Tester une requete simple: `up`
4. Verifier les logs: `docker logs rte-grafana`

### Metriques manquantes

```bash
# Verifier que prometheus_client est installe
pip list | grep prometheus

# Redemarrer l'API
docker-compose restart api
```
