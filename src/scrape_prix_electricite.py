"""
Scraping des prix spot électricité France
Sources : ENTSO-E API (primaire) → Selenium éCO2mix (secondaire) → Données synthétiques (fallback)
"""

import os
import sqlite3
import time

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()


def fetch_prices_energy_charts(start_date, end_date):
    """
    Récupère les prix spot Day-Ahead France depuis energy-charts.info (Fraunhofer ISE)
    Source : données EPEX SPOT, API publique sans authentification

    Args:
        start_date: Date début YYYY-MM-DD
        end_date: Date fin YYYY-MM-DD

    Returns:
        DataFrame avec datetime et spot_price_eur_mwh
    """
    print("  Appel API energy-charts.info (Fraunhofer ISE)...")

    url = "https://api.energy-charts.info/price"
    params = {
        "bzn": "FR",
        "start": f"{start_date}T00:00:00+00:00",
        "end": f"{end_date.split()[0]}T23:59:59+00:00",
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    # Conversion timestamps Unix → datetime
    df = pd.DataFrame({
        "datetime": pd.to_datetime(data["unix_seconds"], unit="s", utc=True),
        "spot_price_eur_mwh": data["price"],
    })

    # Suppression du fuseau horaire pour cohérence avec le reste du projet
    df["datetime"] = df["datetime"].dt.tz_convert("Europe/Paris").dt.tz_localize(None)  # type: ignore[union-attr]
    df["spot_price_eur_mwh"] = df["spot_price_eur_mwh"].round(2)

    # Supprimer les valeurs nulles (données manquantes dans l'API)
    df = df.dropna(subset=["spot_price_eur_mwh"])

    print(f"  {len(df)} prix réels récupérés depuis energy-charts.info")
    return df


def scrape_with_selenium(start_date, end_date):
    """
    Scraping des prix éCO2mix via Selenium (page JavaScript dynamique)
    Source : https://www.rte-france.com/eco2mix/les-donnees-de-marche

    Args:
        start_date: Date début YYYY-MM-DD
        end_date: Date fin YYYY-MM-DD

    Returns:
        DataFrame avec datetime et spot_price_eur_mwh, ou None si échec
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    from webdriver_manager.chrome import ChromeDriverManager

    print("  Lancement Selenium (headless Chrome)...")

    options = webdriver.ChromeOptions() # type: ignore
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    ) # type: ignore

    try:
        url = "https://www.rte-france.com/eco2mix/les-donnees-de-marche"
        print(f"  Chargement : {url}")
        driver.get(url)

        # Attendre que la page JavaScript se charge
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(3)

        print("  Page éCO2mix chargée")
        print("  (Extraction des sélecteurs à adapter selon la structure réelle de la page)")

        # Note : Les sélecteurs CSS/XPath dépendent de la structure exacte de la page RTE.
        # En production, inspecter le DOM avec les DevTools pour identifier les bons sélecteurs.
        # Exemple de structure attendue :
        # rows = driver.find_elements(By.CSS_SELECTOR, "table.market-data tr")
        # for row in rows: extraire datetime + prix

        return None  # Retourner None si l'extraction complète n'est pas encore implémentée

    except Exception as e:
        print(f"  Selenium échoué : {e}")
        return None
    finally:
        driver.quit()


def generate_synthetic_prices(start_date, end_date):
    """
    Génère des prix spot synthétiques réalistes (fallback)
    Basés sur les patterns réels France 2024-2026 : 60-120 EUR/MWh

    Args:
        start_date: Date début YYYY-MM-DD
        end_date: Date fin YYYY-MM-DD

    Returns:
        DataFrame avec datetime et spot_price_eur_mwh
    """
    print("  Génération de prix synthétiques (fallback)...")
    date_range = pd.date_range(start=start_date, end=end_date, freq="h")

    base_price = 80  # Prix de base EUR/MWh

    # Variations horaires (heures pleines plus chères)
    hourly_variation = [
        base_price + 20 * (1 if 8 <= h <= 20 else 0.5) for h in range(24)
    ]

    np.random.seed(42)
    spot_prices = []

    for dt in date_range:
        hour_price = hourly_variation[dt.hour]
        variation = np.random.normal(0, 10)

        # Weekend moins cher
        if dt.dayofweek >= 5:
            hour_price *= 0.85

        final_price = max(30, hour_price + variation)
        spot_prices.append(final_price)

    df = pd.DataFrame({"datetime": date_range, "spot_price_eur_mwh": spot_prices})
    df["spot_price_eur_mwh"] = df["spot_price_eur_mwh"].round(2)

    print(f"  {len(df)} prix synthétiques générés")
    return df


def scrape_spot_prices(start_date, end_date):
    """
    Orchestre la récupération des prix : ENTSO-E → Selenium → Synthétique

    Args:
        start_date: Date début YYYY-MM-DD
        end_date: Date fin YYYY-MM-DD

    Returns:
        DataFrame avec datetime et spot_price_eur_mwh
    """
    print(f"Récupération prix spot électricité {start_date} → {end_date}...")

    # 1er choix : API energy-charts.info (Fraunhofer ISE — données EPEX SPOT)
    try:
        df = fetch_prices_energy_charts(start_date, end_date)
        print("  Source : energy-charts.info (données réelles EPEX SPOT)")
        return df
    except Exception as e:
        print(f"  energy-charts.info échoué : {e}")

    # second choix:: Selenium éCO2mix
    try:
        df = scrape_with_selenium(start_date, end_date)
        if df is not None:
            print("  Source : Selenium éCO2mix (données réelles)")
            return df
        print("  Selenium : page chargée mais extraction non complète")
    except Exception as e:
        print(f"  Selenium échoué : {e}")

    # Fallback : données synthétiques
    print("  Source : données synthétiques")
    return generate_synthetic_prices(start_date, end_date)


def validate_price_data(df):
    """
    Validation et nettoyage des données scrapées

    Args:
        df: DataFrame prix

    Returns:
        DataFrame nettoyé
    """
    print("\nValidation des données...")

    # Vérifier valeurs manquantes
    missing = df.isnull().sum()
    if missing.any():
        print(f"  Valeurs manquantes : {missing.sum()}")
        df = df.dropna()

    # Vérifier plages de valeurs réalistes (prix électricité France)
    invalid_prices = (df["spot_price_eur_mwh"] < 0) | (df["spot_price_eur_mwh"] > 500)
    if invalid_prices.any():
        print(f"  Valeurs aberrantes : {invalid_prices.sum()} (remplacées par médiane)")
        df.loc[invalid_prices, "spot_price_eur_mwh"] = df["spot_price_eur_mwh"].median()

    # Supprimer doublons
    before = len(df)
    df = df.drop_duplicates(subset=["datetime"])
    if len(df) < before:
        print(f"  {before - len(df)} doublons supprimés")

    print(f"  Validation OK — {len(df)} enregistrements valides")
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
        with engine.connect() as conn:
            df.to_sql("spot_prices", conn, if_exists="replace", index=False)
            count = pd.read_sql(
                "SELECT COUNT(*) as total FROM spot_prices", conn
            ).iloc[0]["total"]
    else:
        db_path = os.path.abspath("database/rte_consommation.db")
        with sqlite3.connect(db_path) as conn:
            df.to_sql("spot_prices", conn, if_exists="replace", index=False)
            count = pd.read_sql(
                "SELECT COUNT(*) as total FROM spot_prices", conn
            ).iloc[0]["total"]
    print(f"  {count} enregistrements en base")


def save_to_csv(df, filename="data/spot_prices.csv"):
    """Sauvegarde en CSV"""
    os.makedirs("data", exist_ok=True)
    df.to_csv(filename, index=False)
    print(f"  Sauvegarde : {filename}")


if __name__ == "__main__":
    print("=" * 60)
    print("   Scraping prix spot électricité France")
    print("   energy-charts.info (EPEX SPOT) → Selenium éCO2mix → Synthétique")
    print("=" * 60 + "\n")

    start = "2026-01-01"
    end = "2026-02-15 23:00:00"

    df_prices = scrape_spot_prices(start, end)
    df_prices = validate_price_data(df_prices)

    print("\n" + "=" * 60)
    print("   Statistiques prix spot")
    print("=" * 60)
    print(f"Prix moyen  : {df_prices['spot_price_eur_mwh'].mean():.2f} EUR/MWh")
    print(f"Prix min    : {df_prices['spot_price_eur_mwh'].min():.2f} EUR/MWh")
    print(f"Prix max    : {df_prices['spot_price_eur_mwh'].max():.2f} EUR/MWh")
    print(f"Écart-type  : {df_prices['spot_price_eur_mwh'].std():.2f} EUR/MWh")

    save_to_csv(df_prices)
    database_type = os.getenv("DATABASE_TYPE", "sqlite")
    save_to_database(df_prices, database_type)

    print("\n" + "=" * 60)
    print("   Scraping terminé")
    print("=" * 60)
