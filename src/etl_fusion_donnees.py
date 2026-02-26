"""
Pipeline ETL - Fusion données consommation multi-sources
Compétence C3 RNCP: Collecter et préparer des données multi-sources
"""

import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()


def get_database_engine():
    """Connexion à la base de données"""
    database_type = os.getenv("DATABASE_TYPE", "sqlite").lower()

    if database_type == "postgresql":
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "rte_consommation")
        user = os.getenv("POSTGRES_USER", "rte_user")
        password = os.getenv("POSTGRES_PASSWORD", "rte_secure_password")
        conn_string = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    else:
        db_path = os.path.abspath("database/rte_consommation.db")
        conn_string = f"sqlite:///{db_path}"

    return create_engine(conn_string)


def extract_data():
    """
    Extraction des données depuis 3 types de sources différentes

    Returns:
        tuple: (df_consumption, df_calendar, df_prices)
    """
    print("=== EXTRACT - Extraction des données ===\n")

    engine = get_database_engine()

    # Extraction consommation (source Type 1 : API RTE)
    print("Extraction consommation [SOURCE: API RTE]...")
    df_consumption = pd.read_sql("SELECT * FROM consumption ORDER BY datetime", engine)
    print(f"  {len(df_consumption)} enregistrements consommation")

    # Extraction calendrier jours fériés (source Type 2 : Fichier CSV)
    print("Extraction calendrier [SOURCE: Fichier CSV]...")
    try:
        df_calendar = pd.read_sql(
            "SELECT * FROM holiday_calendar ORDER BY datetime", engine
        )
        print(f"  {len(df_calendar)} enregistrements calendrier")
    except Exception as e:
        print(f"  Table holiday_calendar non trouvée: {e}")
        print("  Exécuter d'abord: python src/load_jours_feries.py")
        return None, None, None

    # Extraction prix spot (source Type 3 : Web scraping)
    print("Extraction prix spot [SOURCE: Web scraping]...")
    try:
        df_prices = pd.read_sql(
            "SELECT * FROM spot_prices ORDER BY datetime", engine
        )
        print(f"  {len(df_prices)} enregistrements prix spot")
    except Exception as e:
        print(f"  Table spot_prices non trouvée: {e}")
        print("  Exécuter d'abord: python src/scrape_prix_electricite.py")
        return None, None, None

    return df_consumption, df_calendar, df_prices


def transform_data(df_consumption, df_calendar, df_prices):
    """
    Nettoyage, validation et fusion des 3 sources

    Args:
        df_consumption: DataFrame consommation (API)
        df_calendar: DataFrame calendrier fériés (Fichier CSV)
        df_prices: DataFrame prix spot (Web scraping)

    Returns:
        DataFrame fusionné et nettoyé
    """
    print("\n=== TRANSFORM - Transformation des données ===\n")

    # Conversion des types datetime
    df_consumption["datetime"] = pd.to_datetime(df_consumption["datetime"])
    df_calendar["datetime"] = pd.to_datetime(df_calendar["datetime"])
    df_prices["datetime"] = pd.to_datetime(df_prices["datetime"])

    print(f"Période consommation: {df_consumption['datetime'].min()} -> {df_consumption['datetime'].max()}")
    print(f"Période calendrier: {df_calendar['datetime'].min()} -> {df_calendar['datetime'].max()}")
    print(f"Période prix spot: {df_prices['datetime'].min()} -> {df_prices['datetime'].max()}")

    # Fusion consommation + prix spot (INNER JOIN)
    print("\nFusion consommation (API) + prix spot (scraping)...")
    df_merged = pd.merge(
        df_consumption, df_prices, on="datetime", how="inner", suffixes=("", "_prix")
    )
    print(f"  {len(df_merged)} enregistrements après fusion")

    # Fusion + calendrier jours fériés (LEFT JOIN)
    print("Fusion + calendrier (Fichier CSV)...")
    calendar_cols = ["datetime", "is_holiday", "is_school_holiday", "holiday_name"]
    df_merged = pd.merge(
        df_merged, df_calendar[calendar_cols], on="datetime", how="left", suffixes=("", "_cal")
    )
    print(f"  {len(df_merged)} enregistrements après fusion")

    # Suppression des colonnes redondantes
    cols_to_drop = [
        col for col in df_merged.columns
        if col.endswith("_meteo") or col == "created_at"
    ]
    df_merged = df_merged.drop(columns=cols_to_drop, errors="ignore")

    # Création des variables temporelles
    print("\nCréation des variables temporelles...")
    df_merged["hour"] = df_merged["datetime"].dt.hour # type: ignore
    df_merged["day_of_week"] = df_merged["datetime"].dt.dayofweek # type: ignore
    df_merged["month"] = df_merged["datetime"].dt.month # type: ignore
    df_merged["day_of_month"] = df_merged["datetime"].dt.day # type: ignore
    df_merged["is_weekend"] = (df_merged["day_of_week"] >= 5).astype(int)

    # Traitement des valeurs manquantes
    missing = df_merged.isnull().sum()
    if missing.any():
        print(f"\nValeurs manquantes:\n{missing[missing > 0]}")
        df_merged = df_merged.dropna()

    # Remplissage valeurs manquantes pour colonnes calendrier
    df_merged["is_holiday"] = df_merged["is_holiday"].fillna(False).astype(int)
    df_merged["is_school_holiday"] = df_merged["is_school_holiday"].fillna(False).astype(int)
    df_merged["holiday_name"] = df_merged["holiday_name"].fillna("")

    # Statistiques finales
    print("\n=== Statistiques données fusionnées ===")
    print(f"Total enregistrements: {len(df_merged)}")
    print(f"Colonnes: {list(df_merged.columns)}")
    print(f"Prix spot moyen: {df_merged['spot_price_eur_mwh'].mean():.2f} EUR/MWh")

    return df_merged


def load_data(df, table_name="enriched_consumption"):
    """
    Chargement dans la base de données

    Args:
        df: DataFrame à charger
        table_name: Nom de la table destination
    """
    print(f"\n=== LOAD - Chargement dans table '{table_name}' ===\n")

    engine = get_database_engine()

    # Sauvegarde en base
    df.to_sql(table_name, engine, if_exists="replace", index=False)

    # Vérification
    count = pd.read_sql(f"SELECT COUNT(*) as total FROM {table_name}", engine).iloc[0]["total"]
    print(f"  {count} enregistrements chargés")

    # Export CSV
    os.makedirs("data", exist_ok=True)
    csv_path = f"data/{table_name}.csv"
    df.to_csv(csv_path, index=False)
    print(f"  Export CSV: {csv_path}")


def run_etl_pipeline():
    """Exécution complète du pipeline ETL - 3 types de sources"""
    print("=" * 60)
    print("   Pipeline ETL - Fusion 3 types de sources")
    print("   API + Fichier CSV + Web Scraping")
    print("=" * 60 + "\n")

    df_consumption, df_calendar, df_prices = extract_data()

    if df_consumption is None or df_calendar is None or df_prices is None:
        print("\nERREUR: Données source manquantes")
        print("Exécuter dans l'ordre:")
        print("  python src/create_dataset.py")
        print("  python src/load_jours_feries.py")
        print("  python src/scrape_prix_electricite.py")
        return False

    df_enriched = transform_data(df_consumption, df_calendar, df_prices)

    load_data(df_enriched, table_name="enriched_consumption")

    print("\n" + "=" * 60)
    print("        Pipeline ETL terminé avec succès")
    print("        3 types de sources intégrées")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = run_etl_pipeline()
    exit(0 if success else 1)
