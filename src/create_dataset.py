import base64
import os

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

print("Création du dataset...")


def fetch_rte_consumption(start_date, end_date):
    """
    Récupère la consommation depuis l'API RTE officielle avec authentification OAuth2

    Flux OAuth2 :
      1. Encode client_id:client_secret en base64
      2. POST /token/oauth/ → access_token
      3. GET /consumption/v1/consumption avec Bearer token

    Args:
        start_date: Date début YYYY-MM-DD
        end_date: Date fin YYYY-MM-DD

    Returns:
        DataFrame avec datetime et mw_consumption, ou None si échec
    """
    client_id = os.getenv("RTE_CLIENT_ID")
    client_secret = os.getenv("RTE_CLIENT_SECRET")

    if not client_id or not client_secret:
        return None

    print("  Authentification OAuth2 RTE...")

    #  obtenir le token OAuth2
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    token_resp = requests.post(
        "https://digital.iservices.rte-france.com/token/oauth/",
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        timeout=30,
    )
    token_resp.raise_for_status()
    access_token = token_resp.json()["access_token"]
    print("  Token OAuth2 obtenu")

    # appel API short_term (données réalisées temps réel)
    # Endpoint consumption/v1/short_term — retourne la journée courante en pas 15 min
    resp = requests.get(
        "https://digital.iservices.rte-france.com/open_api/consumption/v1/short_term",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    # Parser la réponse RTE — ne garder que le type REALISED
    rows = []
    for bloc in data.get("short_term", []):
        if bloc.get("type") != "REALISED":
            continue
        for val in bloc.get("values", []):
            rows.append({
                "datetime": pd.to_datetime(val["start_date"]).tz_localize(None),
                "mw_consumption": val["value"],
            })

    if not rows:
        print("  RTE API : aucune donnée dans la réponse")
        return None

    df = pd.DataFrame(rows)
    df["datetime"] = df["datetime"].dt.floor("h") # type: ignore
    df = df.groupby("datetime")["mw_consumption"].mean().reset_index()
    df["mw_consumption"] = df["mw_consumption"].round(0)

    print(f"  {len(df)} heures récupérées depuis l'API RTE officielle")
    return df


def fetch_odre_consumption(start_date, end_date):
    """
    Récupère la consommation réelle depuis l'API ODRE éCO2mix (sans authentification)
    Données RTE publiées sur la plateforme open data gouvernementale

    Args:
        start_date: Date début YYYY-MM-DD
        end_date: Date fin YYYY-MM-DD

    Returns:
        DataFrame avec datetime et mw_consumption, ou None si échec
    """
    url = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/records"
    all_records = []
    offset = 0
    limit = 100

    print(f"  Récupération ODRE éCO2mix {start_date} → {end_date}...")

    while True:
        params = {
            "limit": limit,
            "offset": offset,
            "where": (
                f"consommation IS NOT NULL "
                f"AND date_heure >= '{start_date}T00:00:00+00:00' "
                f"AND date_heure <= '{end_date}T23:59:59+00:00'"
            ),
            "order_by": "date_heure asc",
            "select": "date_heure,consommation",
        }
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        records = data["results"]
        all_records.extend(records)

        if len(records) < limit:
            break
        offset += limit

    if not all_records:
        return None

    df = pd.DataFrame(all_records)
    df["datetime"] = pd.to_datetime(df["date_heure"]).dt.tz_localize(None)
    df = df.rename(columns={"consommation": "mw_consumption"})

    # Agrégation 15 minutes → horaire
    df["datetime"] = df["datetime"].dt.floor("h") # type: ignore
    df = df.groupby("datetime")["mw_consumption"].mean().reset_index()
    df["mw_consumption"] = df["mw_consumption"].round(0)

    print(f"  {len(df)} heures de consommation réelle récupérées")
    return df


# Données synthétiques (fallback si toutes les APIs indisponibles)
dates = pd.date_range("2025-01-01", periods=10000, freq="H")
conso = (
    45000 + 12000 * np.sin(2 * np.pi * dates.hour / 24) + np.random.normal(0, 1500, len(dates))
)

df = pd.DataFrame({"datetime": dates, "mw_consumption": conso.round(0)})

# Source 1 : API RTE officielle (OAuth2 — priorité si credentials disponibles)
try:
    df_rte = fetch_rte_consumption("2026-01-01", "2026-02-15")
    if df_rte is not None and len(df_rte) > 0:
        print(f"RTE API OK — {len(df_rte)} heures temps réel (journée en cours)")
        # RTE short_term = données du jour uniquement → ODRE pour l'historique
        raise ValueError("données temps réel uniquement, historique via ODRE")
except Exception as e:
    print(f"RTE API échouée: {e}")

    # Source 2 : ODRE éCO2mix (fallback sans authentification)
    try:
        df_odre = fetch_odre_consumption("2026-01-01", "2026-02-15")
        if df_odre is not None and len(df_odre) > 100:
            df = df_odre
            print("ODRE OK, données éCO2mix utilisées")
        else:
            print("ODRE : données insuffisantes, données synthétiques utilisées")
    except Exception as e2:
        print(f"ODRE échoué: {e2}, données synthétiques utilisées")

os.makedirs("data", exist_ok=True)
os.makedirs("database", exist_ok=True)

df.to_csv("data/rte_consumption.csv", index=False)

db_path = os.path.abspath("database/rte_consommation.db")
engine = create_engine(f"sqlite:///{db_path}")
df.to_sql("consumption", engine, if_exists="replace", index=False)

print("Dataset créé")
print(f"Lignes: {len(df)}")
print(f"DB: {db_path}")
