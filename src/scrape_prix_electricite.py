"""
Scrapping web des prix spot electricite France
Source: Web scraping de donnees publiques RTE
"""

import os
import re
from datetime import datetime, timedelta

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()


def scrape_prix_spot_simule(start_date, end_date):
    """
    Simule le scrapping de prix spot electricite
    (En production, scrapper depuis site EPEX/Powernext)

    Args:
        start_date: Date debut YYYY-MM-DD
        end_date: Date fin YYYY-MM-DD

    Returns:
        DataFrame avec datetime et prix_spot_eur_mwh
    """
    print(f"Scrapping prix spot electricite {start_date} -> {end_date}...")
    print("  Source: Donnees publiques simulees (remplacer par vrai scrapper)")

    # Generation de prix spot realistes bases sur patterns reels
    # Prix moyens France 2024-2026 : 60-120 EUR/MWh
    date_range = pd.date_range(start=start_date, end=end_date, freq="h")

    prix_base = 80  # Prix de base EUR/MWh

    # Variations horaires (heures pleines plus cheres)
    variation_horaire = [
        prix_base + 20 * (1 if 8 <= h <= 20 else 0.5) for h in range(24)
    ]

    # Generer prix avec variations
    import numpy as np

    np.random.seed(42)
    prix_spot = []

    for dt in date_range:
        heure = dt.hour
        prix_heure = variation_horaire[heure]

        # Ajouter variations aleatoires
        variation = np.random.normal(0, 10)

        # Weekend moins cher
        if dt.dayofweek >= 5:
            prix_heure *= 0.85

        prix_final = max(30, prix_heure + variation)  # Prix min 30 EUR/MWh
        prix_spot.append(prix_final)

    df = pd.DataFrame({"datetime": date_range, "prix_spot_eur_mwh": prix_spot})

    df["prix_spot_eur_mwh"] = df["prix_spot_eur_mwh"].round(2)

    print(f"  {len(df)} prix scrappe")

    return df


def scrape_prix_rte_web_simule():
    """
    Exemple de scrapping HTML simule
    En production: scrapper depuis https://www.rte-france.com/eco2mix

    Returns:
        DataFrame avec donnees scrappees
    """
    print("\nSimulation scrapping web HTML...")

    # En production, faire:
    # url = "https://www.rte-france.com/eco2mix/les-donnees-de-marche"
    # response = requests.get(url)
    # soup = BeautifulSoup(response.content, 'html.parser')
    # Extraire donnees depuis les tableaux HTML

    # Pour demo, generer donnees
    print("  (En production: parser HTML avec BeautifulSoup)")
    print("  Simulation OK")

    return None


def validate_prix_data(df):
    """
    Validation et nettoyage des donnees scrappees

    Args:
        df: DataFrame prix

    Returns:
        DataFrame nettoye
    """
    print("\nValidation des donnees scrappees...")

    # Verifier valeurs manquantes
    missing = df.isnull().sum()
    if missing.any():
        print(f"  Valeurs manquantes: {missing.sum()}")
        df = df.dropna()

    # Verifier plages de valeurs realistes (prix electricite France)
    # Prix spot historiques: 20-500 EUR/MWh (pics exceptionnels)
    invalid_prix = (df["prix_spot_eur_mwh"] < 0) | (df["prix_spot_eur_mwh"] > 500)

    if invalid_prix.any():
        print(
            f"  Valeurs aberrantes detectees: {invalid_prix.sum()} (prix < 0 ou > 500)"
        )
        # Remplacer par mediane
        df.loc[invalid_prix, "prix_spot_eur_mwh"] = df["prix_spot_eur_mwh"].median()

    # Supprimer doublons
    before = len(df)
    df = df.drop_duplicates(subset=["datetime"])
    if len(df) < before:
        print(f"  {before - len(df)} doublons supprimes")

    print(f"  Validation OK - {len(df)} enregistrements valides")
    return df


def save_to_database(df, database_type="sqlite"):
    """
    Sauvegarde les prix spot dans la base

    Args:
        df: DataFrame prix
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
    df.to_sql("prix_spot_electricite", engine, if_exists="replace", index=False)

    # Verifier
    count = pd.read_sql(
        "SELECT COUNT(*) as total FROM prix_spot_electricite", engine
    ).iloc[0]["total"]
    print(f"  {count} enregistrements prix spot en base")


def save_to_csv(df, filename="data/prix_spot_electricite.csv"):
    """Sauvegarde en CSV"""
    os.makedirs("data", exist_ok=True)
    df.to_csv(filename, index=False)
    print(f"  Sauvegarde: {filename}")


if __name__ == "__main__":
    print("=" * 60)
    print("   Scrapping web - Prix spot electricite France")
    print("=" * 60 + "\n")

    # Periode correspondant aux donnees de consommation
    start = "2026-01-01"
    end = "2026-01-21 23:00:00"

    # Scrapping (simule)
    df_prix = scrape_prix_spot_simule(start, end)

    # Demo scrapping HTML
    scrape_prix_rte_web_simule()

    if df_prix is not None:
        # Validation
        df_prix = validate_prix_data(df_prix)

        # Statistiques descriptives
        print("\n" + "=" * 60)
        print("   Statistiques prix spot")
        print("=" * 60)
        print(f"Prix moyen: {df_prix['prix_spot_eur_mwh'].mean():.2f} EUR/MWh")
        print(f"Prix min: {df_prix['prix_spot_eur_mwh'].min():.2f} EUR/MWh")
        print(f"Prix max: {df_prix['prix_spot_eur_mwh'].max():.2f} EUR/MWh")
        print(f"Ecart-type: {df_prix['prix_spot_eur_mwh'].std():.2f} EUR/MWh")

        # Sauvegarde
        save_to_csv(df_prix)
        database_type = os.getenv("DATABASE_TYPE", "sqlite")
        save_to_database(df_prix, database_type)

        print("\n" + "=" * 60)
        print("   Scrapping termine")
        print("=" * 60)
    else:
        print("\nEchec du scrapping")
        exit(1)
