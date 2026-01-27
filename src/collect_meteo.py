"""
Collecte de données météo via API Open-Meteo
Source multi-données pour enrichir les prédictions de consommation
"""

import os
from datetime import datetime, timedelta

import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()


def get_meteo_data(start_date, end_date, latitude=48.8566, longitude=2.3522):
    """
    Collecte données météo France via Open-Meteo API (gratuite)

    Args:
        start_date: Date début YYYY-MM-DD
        end_date: Date fin YYYY-MM-DD
        latitude: Latitude (défaut: Paris)
        longitude: Longitude (défaut: Paris)

    Returns:
        DataFrame avec datetime, temperature, vent, ensoleillement
    """
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,windspeed_10m,cloudcover",
        "timezone": "Europe/Paris",
    }

    print(f"Collecte météo {start_date} -> {end_date}...")

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Extraction des données horaires
        hourly = data.get("hourly", {})

        df = pd.DataFrame(
            {
                "datetime": pd.to_datetime(hourly["time"]),
                "temperature": hourly["temperature_2m"],
                "vent": hourly["windspeed_10m"],
                "couverture_nuageuse": hourly["cloudcover"],
            }
        )

        # Calculer ensoleillement (inverse de la couverture nuageuse)
        df["ensoleillement"] = 100 - df["couverture_nuageuse"]

        # Supprimer la colonne temporaire
        df = df.drop(columns=["couverture_nuageuse"])

        print(f"  {len(df)} enregistrements météo collectés")
        return df

    except requests.exceptions.RequestException as e:
        print(f"Erreur API Open-Meteo: {e}")
        return None


def validate_meteo_data(df):
    """
    Validation et nettoyage des données météo

    Args:
        df: DataFrame météo

    Returns:
        DataFrame nettoyé
    """
    print("\nValidation des données météo...")

    # Vérifier valeurs manquantes
    missing = df.isnull().sum()
    if missing.any():
        print(f"  Valeurs manquantes détectées:\n{missing[missing > 0]}")

        # Interpolation linéaire pour combler les trous
        df["temperature"] = df["temperature"].interpolate(method="linear")
        df["vent"] = df["vent"].interpolate(method="linear")
        df["ensoleillement"] = df["ensoleillement"].interpolate(method="linear")

        print("  Interpolation appliquée")

    # Vérifier plages de valeurs réalistes
    invalid_temp = (df["temperature"] < -30) | (df["temperature"] > 50)
    invalid_wind = (df["vent"] < 0) | (df["vent"] > 200)
    invalid_sun = (df["ensoleillement"] < 0) | (df["ensoleillement"] > 100)

    if invalid_temp.any() or invalid_wind.any() or invalid_sun.any():
        print(
            f"  Valeurs aberrantes détectées: {invalid_temp.sum() + invalid_wind.sum() + invalid_sun.sum()}"
        )
        # Remplacer par la médiane
        df.loc[invalid_temp, "temperature"] = df["temperature"].median()
        df.loc[invalid_wind, "vent"] = df["vent"].median()
        df.loc[invalid_sun, "ensoleillement"] = df["ensoleillement"].median()

    # Supprimer doublons
    before = len(df)
    df = df.drop_duplicates(subset=["datetime"])
    if len(df) < before:
        print(f"  {before - len(df)} doublons supprimés")

    print(f"  Validation OK - {len(df)} enregistrements valides")
    return df


def save_to_database(df, database_type="sqlite"):
    """
    Sauvegarde les données météo dans la base

    Args:
        df: DataFrame météo
        database_type: 'sqlite' ou 'postgresql'
    """
    print(f"\nSauvegarde dans base {database_type}...")

    if database_type == "postgresql":
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "rte_consommation")
        user = os.getenv("POSTGRES_USER", "rte_user")
        password = os.getenv("POSTGRES_PASSWORD", "rte_secure_password")
        conn_string = f"postgresql://{user}:{password}@{host}:{port}/{db}"
        engine = create_engine(conn_string)
    else:
        db_path = os.path.abspath("database/rte_consommation.db")
        engine = create_engine(f"sqlite:///{db_path}")

    # Sauvegarder
    df.to_sql("meteo", engine, if_exists="replace", index=False)

    # Vérifier
    count = pd.read_sql("SELECT COUNT(*) as total FROM meteo", engine).iloc[0]["total"]
    print(f"  {count} enregistrements météo en base")


def save_to_csv(df, filename="data/meteo.csv"):
    """Sauvegarde en CSV"""
    os.makedirs("data", exist_ok=True)
    df.to_csv(filename, index=False)
    print(f"  Sauvegardé: {filename}")


if __name__ == "__main__":
    print("=== Collecte données météo ===\n")

    # Période correspondant aux données de consommation
    start = "2026-01-01"
    end = "2026-01-21"

    # Collecte
    df_meteo = get_meteo_data(start, end)

    if df_meteo is not None:
        # Validation
        df_meteo = validate_meteo_data(df_meteo)

        # Statistiques descriptives
        print("\n=== Statistiques météo ===")
        print(f"Température moyenne: {df_meteo['temperature'].mean():.1f}°C")
        print(f"Température min: {df_meteo['temperature'].min():.1f}°C")
        print(f"Température max: {df_meteo['temperature'].max():.1f}°C")
        print(f"Vent moyen: {df_meteo['vent'].mean():.1f} km/h")
        print(f"Ensoleillement moyen: {df_meteo['ensoleillement'].mean():.1f}%")

        # Sauvegarde
        save_to_csv(df_meteo)
        database_type = os.getenv("DATABASE_TYPE", "sqlite")
        save_to_database(df_meteo, database_type)

        print("\n=== Collecte terminée ===")
    else:
        print("\nÉchec de la collecte météo")
        exit(1)
