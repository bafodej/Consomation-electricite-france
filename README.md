# Consommation Électricité France - RTE Data Analysis/ML

## 🎯 Objectif
Analyse conso électrique France (RTE éCO2mix) + impact IA/data centers (vidéos).

## 📊 Données sources
- `data/conso_rte_france.csv`: Temps réel MW [RTE][web:36]
- `data/conso_recent_2026.csv`: Prévisions Jan 2026
- 95% bas carbone 2024 (536 TWh)[web:30]

## 🚀 Quickstart
```bash
git clone https://github.com/bafodej/Consomation-electricite-france
cd Consomation-electricite-france
pip install -r requirements.txt
python src/analyse_rte.py
