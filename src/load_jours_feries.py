"""
Chargement et traitement des jours fériés depuis fichier texte CSV
Source de données: Fichier texte local
"""

import os
from datetime import datetime, timedelta

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()


def load_jours_feries_from_file(filepath="data/jours_feries_2026.csv"):
    """
    Charge les jours fériés depuis fichier CSV

    Args:
        filepath: Chemin vers le fichier CSV

    Returns:
        DataFrame avec les jours fériés
    """
    print(f"Chargement fichier: {filepath}")

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Fichier introuvable: {filepath}")

    # Lecture fichier CSV
    df = pd.read_csv(filepath)

    # Conversion date
    df["date"] = pd.to_datetime(df["date"])

    print(f"  {len(df)} jours fériés chargés")
    print(f"  Colonnes: {list(df.columns)}")

    return df


def enrich_with_vacances_scolaires(df_feries):
    """
    Enrichit avec les périodes de vacances scolaires 2026 (Zone C - Paris)

    Args:
        df_feries: DataFrame jours fériés

    Returns:
        DataFrame enrichi avec vacances
    """
    print("\nAjout des vacances scolaires 2026...")

    # Périodes vacances scolaires 2026 (Zone C - Île-de-France)
    vacances = [
        ("2026-02-21", "2026-03-08", "Vacances d'hiver"),
        ("2026-04-18", "2026-05-03", "Vacances de printemps"),
        ("2026-07-04", "2026-08-31", "Vacances d'été"),
        ("2026-10-24", "2026-11-08", "Vacances de la Toussaint"),
        ("2026-12-19", "2026-01-03", "Vacances de Noël"),
    ]

    vacances_rows = []
    for start, end, nom in vacances:
        start_date = pd.to_datetime(start)
        end_date = pd.to_datetime(end)

        # Générer toutes les dates de la période
        date_range = pd.date_range(start_date, end_date, freq="D")

        for date in date_range:
            vacances_rows.append({"date": date, "nom_ferie": nom, "type": "vacances"})

    df_vacances = pd.DataFrame(vacances_rows)

    # Fusion avec jours fériés
    df_combined = pd.concat([df_feries, df_vacances], ignore_index=True)
    df_combined = df_combined.sort_values("date").reset_index(drop=True)

    print(f"  {len(df_vacances)} jours de vacances ajoutés")
    print(f"  Total: {len(df_combined)} jours spéciaux")

    return df_combined


def create_hourly_calendar(start_date="2026-01-01", end_date="2026-12-31"):
    """
    Crée un calendrier horaire avec indicateurs jour férié/vacances

    Args:
        start_date: Date de début
        end_date: Date de fin

    Returns:
        DataFrame avec datetime et indicateurs
    """
    print(f"\nCréation calendrier horaire {start_date} -> {end_date}...")

    # Générer toutes les heures
    date_range = pd.date_range(start=start_date, end=f"{end_date} 23:00:00", freq="h")

    df_calendar = pd.DataFrame({"datetime": date_range})
    df_calendar["date"] = df_calendar["datetime"].dt.date
    df_calendar["date"] = pd.to_datetime(df_calendar["date"])

    print(f"  {len(df_calendar)} heures générées")

    return df_calendar


def merge_calendar_with_feries(df_calendar, df_feries):
    """
    Fusionne le calendrier avec les jours fériés

    Args:
        df_calendar: Calendrier horaire
        df_feries: Jours fériés et vacances

    Returns:
        DataFrame enrichi
    """
    print("\nFusion calendrier avec jours fériés...")

    # Créer indicateurs
    df_feries["est_ferie"] = (df_feries["type"] == "fixe") | (
        df_feries["type"] == "mobile"
    )
    df_feries["est_vacances"] = df_feries["type"] == "vacances"

    # Grouper par date (plusieurs types possibles pour même jour)
    df_feries_agg = (
        df_feries.groupby("date")
        .agg({"est_ferie": "max", "est_vacances": "max", "nom_ferie": "first"})
        .reset_index()
    )

    # Fusion avec calendrier
    df_merged = pd.merge(df_calendar, df_feries_agg, on="date", how="left")

    # Remplir NaN avec False/vide
    df_merged["est_ferie"] = df_merged["est_ferie"].fillna(False).astype(bool)
    df_merged["est_vacances"] = df_merged["est_vacances"].fillna(False).astype(bool)
    df_merged["nom_ferie"] = df_merged["nom_ferie"].fillna("")

    # Statistiques
    nb_feries = df_merged["est_ferie"].sum()
    nb_vacances = df_merged["est_vacances"].sum()

    print(f"  Heures en jour férié: {nb_feries}")
    print(f"  Heures en vacances: {nb_vacances}")

    return df_merged


def save_to_database(df, table_name="calendrier_feries"):
    """
    Sauvegarde dans la base de données

    Args:
        df: DataFrame calendrier
        table_name: Nom de la table
    """
    print(f"\nSauvegarde dans table '{table_name}'...")

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

    engine = create_engine(conn_string)

    # Sauvegarder
    df.to_sql(table_name, engine, if_exists="replace", index=False)

    # Vérifier
    count = pd.read_sql(f"SELECT COUNT(*) as total FROM {table_name}", engine).iloc[0][
        "total"
    ]
    print(f"  {count} enregistrements sauvegardés")


if __name__ == "__main__":
    print("=" * 50)
    print("   Chargement jours feries (fichier CSV)")
    print("=" * 50 + "\n")

    # 1. Charger fichier CSV
    df_feries = load_jours_feries_from_file("data/jours_feries_2026.csv")

    # 2. Enrichir avec vacances scolaires
    df_feries_enrichi = enrich_with_vacances_scolaires(df_feries)

    print("\n=== Aperçu jours fériés ===")
    print(df_feries_enrichi.head(15))

    # 3. Créer calendrier horaire
    df_calendar = create_hourly_calendar("2026-01-01", "2026-12-31")

    # 4. Fusionner
    df_final = merge_calendar_with_feries(df_calendar, df_feries_enrichi)

    # 5. Sauvegarder
    save_to_database(df_final, "calendrier_feries")

    # Export CSV
    output_csv = "data/calendrier_feries_2026.csv"
    df_final.to_csv(output_csv, index=False)
    print(f"\nExport CSV: {output_csv}")

    print("\n" + "=" * 50)
    print("           Traitement termine")
    print("=" * 50)
