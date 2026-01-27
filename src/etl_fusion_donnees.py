"""
Pipeline ETL - Fusion données consommation + météo
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
    Extract: Extraction des données depuis les sources

    Returns:
        tuple: (df_conso, df_meteo)
    """
    print("=== EXTRACT - Extraction des données ===\n")

    engine = get_database_engine()

    # Extraction consommation
    print("Extraction table consommation...")
    df_conso = pd.read_sql("SELECT * FROM consommation ORDER BY datetime", engine)
    print(f"  {len(df_conso)} enregistrements consommation")

    # Extraction météo
    print("Extraction table meteo...")
    try:
        df_meteo = pd.read_sql("SELECT * FROM meteo ORDER BY datetime", engine)
        print(f"  {len(df_meteo)} enregistrements météo")
    except Exception as e:
        print(f"  Table meteo non trouvée: {e}")
        print("  Exécuter d'abord: python src/collect_meteo.py")
        return None, None

    return df_conso, df_meteo


def transform_data(df_conso, df_meteo):
    """
    Transform: Nettoyage, validation, fusion

    Args:
        df_conso: DataFrame consommation
        df_meteo: DataFrame météo

    Returns:
        DataFrame fusionné et nettoyé
    """
    print("\n=== TRANSFORM - Transformation des données ===\n")

    # Conversion types datetime
    df_conso["datetime"] = pd.to_datetime(df_conso["datetime"])
    df_meteo["datetime"] = pd.to_datetime(df_meteo["datetime"])

    print(
        f"Période consommation: {df_conso['datetime'].min()} -> {df_conso['datetime'].max()}"
    )
    print(
        f"Période météo: {df_meteo['datetime'].min()} -> {df_meteo['datetime'].max()}"
    )

    # Fusion sur datetime (INNER JOIN)
    print("\nFusion des données...")
    df_merged = pd.merge(
        df_conso, df_meteo, on="datetime", how="inner", suffixes=("", "_meteo")
    )

    print(f"  {len(df_merged)} enregistrements après fusion")

    # Supprimer colonnes redondantes
    cols_to_drop = [
        col
        for col in df_merged.columns
        if col.endswith("_meteo") or col == "created_at"
    ]
    df_merged = df_merged.drop(columns=cols_to_drop, errors="ignore")

    # Créer features temporelles
    print("\nCréation features temporelles...")
    df_merged["heure"] = df_merged["datetime"].dt.hour
    df_merged["jour_semaine"] = df_merged["datetime"].dt.dayofweek
    df_merged["mois"] = df_merged["datetime"].dt.month
    df_merged["jour_mois"] = df_merged["datetime"].dt.day
    df_merged["est_weekend"] = (df_merged["jour_semaine"] >= 5).astype(int)

    # Vérifier valeurs manquantes
    missing = df_merged.isnull().sum()
    if missing.any():
        print(f"\nValeurs manquantes:\n{missing[missing > 0]}")
        df_merged = df_merged.dropna()
        print(f"  Lignes supprimées: {len(df_conso) - len(df_merged)}")

    # Statistiques finales
    print("\n=== Statistiques données fusionnées ===")
    print(f"Total enregistrements: {len(df_merged)}")
    print(f"Colonnes: {list(df_merged.columns)}")
    print("\nCorrélations avec consommation:")

    corr_vars = ["temperature", "vent", "ensoleillement", "heure", "jour_semaine"]
    for var in corr_vars:
        if var in df_merged.columns:
            corr = df_merged["mw_conso"].corr(df_merged[var])
            print(f"  {var}: {corr:.3f}")

    return df_merged


def load_data(df, table_name="conso_meteo_enrichi"):
    """
    Load: Chargement dans la base de données

    Args:
        df: DataFrame à charger
        table_name: Nom de la table destination
    """
    print(f"\n=== LOAD - Chargement dans table '{table_name}' ===\n")

    engine = get_database_engine()

    # Sauvegarde en base
    df.to_sql(table_name, engine, if_exists="replace", index=False)

    # Vérification
    count = pd.read_sql(f"SELECT COUNT(*) as total FROM {table_name}", engine).iloc[0][
        "total"
    ]
    print(f"  {count} enregistrements chargés")

    # Sauvegarde CSV
    os.makedirs("data", exist_ok=True)
    csv_path = f"data/{table_name}.csv"
    df.to_csv(csv_path, index=False)
    print(f"  Export CSV: {csv_path}")


def run_etl_pipeline():
    """Exécution complète du pipeline ETL"""
    print("╔════════════════════════════════════════════╗")
    print("║   Pipeline ETL - Fusion Multi-Sources     ║")
    print("║   Consommation RTE + Météo Open-Meteo     ║")
    print("╚════════════════════════════════════════════╝\n")

    # EXTRACT
    df_conso, df_meteo = extract_data()

    if df_conso is None or df_meteo is None:
        print("\nERREUR: Données source manquantes")
        return False

    # TRANSFORM
    df_enrichi = transform_data(df_conso, df_meteo)

    # LOAD
    load_data(df_enrichi, table_name="conso_meteo_enrichi")

    print("\n╔════════════════════════════════════════════╗")
    print("║        Pipeline ETL terminé avec succès   ║")
    print("╚════════════════════════════════════════════╝")

    return True


if __name__ == "__main__":
    success = run_etl_pipeline()
    exit(0 if success else 1)
