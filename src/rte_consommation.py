import pandas as pd
import requests

url = "https://odre.opendatasoft.com/api/records/1.0/search/"
params = {
    "dataset": "eco2mix-national-cons-def",
    "rows": 500,
    "sort": "-date_heure",
    "refine.perimetre": "France",
}

resp = requests.get(url, params=params)
data = resp.json()

# Extraction fields
records = []
for r in data["records"]:
    fields = r["fields"]
    fields["recordid"] = r["recordid"]
    records.append(fields)

df = pd.DataFrame(records)
df["date_heure"] = pd.to_datetime(df["date_heure"])
df = df.sort_values("date_heure", ascending=False)

# Conso (prévisions MW)
print(" Colonnes:", df.columns.tolist())
print(df[["date_heure", "prevision_j", "prevision_j1"]].head())

df.to_csv("conso_rte_france.csv", index=False)
print(f" {len(df)} lignes → conso_rte_france.csv")


#  Données récentes + Graph
def get_recent_conso():
    params = {
        "dataset": "eco2mix-national-tr",  # Temps réel
        "rows": 1000,
        "sort": "-date_heure",
        "refine.perimetre": "France",
    }
    resp = requests.get(
        "https://odre.opendatasoft.com/api/records/1.0/search/", params=params
    )
    data = resp.json()

    records = [
        {
            "date_heure": r["fields"]["date_heure"],
            "consommation": r["fields"].get("consommation", 0),
            "prevision_j": r["fields"].get("prevision_j", 0),
        }
        for r in data["records"]
    ]

    return pd.DataFrame(records).dropna().tail(168)  # 7 jours


recent_df = get_recent_conso()
recent_df["date_heure"] = pd.to_datetime(recent_df["date_heure"])
recent_df.to_csv("conso_recent_2026.csv", index=False)

print("\n conso_recent_2026.csv (données fraîches)")
print(recent_df.head())
