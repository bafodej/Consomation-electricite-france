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


def load_holidays_from_file(filepath="data/public_holidays_2026.csv"):
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

    # Conversion date et renommage colonne
    df["date"] = pd.to_datetime(df["date"])
    df = df.rename(columns={"nom_ferie": "holiday_name"})

    print(f"  {len(df)} jours fériés chargés")
    print(f"  Colonnes: {list(df.columns)}")

    return df


def enrich_with_school_holidays(df_holidays):
    """
    Enrichit avec les périodes de vacances scolaires 2026 (Zone C - Paris)

    Args:
        df_holidays: DataFrame jours fériés

    Returns:
        DataFrame enrichi avec vacances
    """
    print("\nAjout des vacances scolaires 2026...")

    # Périodes vacances scolaires 2026 (Zone C - Île-de-France)
    school_holidays = [
        ("2026-02-21", "2026-03-08", "Vacances d'hiver"),
        ("2026-04-18", "2026-05-03", "Vacances de printemps"),
        ("2026-07-04", "2026-08-31", "Vacances d'été"),
        ("2026-10-24", "2026-11-08", "Vacances de la Toussaint"),
        ("2026-12-19", "2026-01-03", "Vacances de Noël"),
    ]

    holiday_rows = []
    for start, end, name in school_holidays:
        start_date = pd.to_datetime(start)
        end_date = pd.to_datetime(end)

        # Générer toutes les dates de la période
        date_range = pd.date_range(start_date, end_date, freq="D")

        for date in date_range:
            holiday_rows.append({"date": date, "holiday_name": name, "type": "vacances"})

    df_school_holidays = pd.DataFrame(holiday_rows)

    # Fusion avec jours fériés
    df_combined = pd.concat([df_holidays, df_school_holidays], ignore_index=True)
    df_combined = df_combined.sort_values("date").reset_index(drop=True)

    print(f"  {len(df_school_holidays)} jours de vacances ajoutés")
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
    df_calendar["date"] = df_calendar["datetime"].dt.date  # type: ignore
    df_calendar["date"] = pd.to_datetime(df_calendar["date"])

    print(f"  {len(df_calendar)} heures générées")

    return df_calendar


def merge_calendar_with_holidays(df_calendar, df_holidays):
    """
    Fusionne le calendrier avec les jours fériés

    Args:
        df_calendar: Calendrier horaire
        df_holidays: Jours fériés et vacances

    Returns:
        DataFrame enrichi
    """
    print("\nFusion calendrier avec jours fériés...")

    # Créer indicateurs binaires
    df_holidays["is_holiday"] = (df_holidays["type"] == "fixe") | (
        df_holidays["type"] == "mobile"
    )
    df_holidays["is_school_holiday"] = df_holidays["type"] == "vacances"

    # Grouper par date (plusieurs types possibles pour même jour)
    df_holidays_agg = (
        df_holidays.groupby("date")
        .agg({"is_holiday": "max", "is_school_holiday": "max", "holiday_name": "first"})
        .reset_index()
    )

    # Fusion avec calendrier
    df_merged = pd.merge(df_calendar, df_holidays_agg, on="date", how="left")

    # Remplir valeurs manquantes
    df_merged["is_holiday"] = df_merged["is_holiday"].fillna(False).astype(bool)
    df_merged["is_school_holiday"] = df_merged["is_school_holiday"].fillna(False).astype(bool)
    df_merged["holiday_name"] = df_merged["holiday_name"].fillna("")

    # Statistiques
    nb_holidays = df_merged["is_holiday"].sum()
    nb_school_holidays = df_merged["is_school_holiday"].sum()

    print(f"  Heures en jour férié: {nb_holidays}")
    print(f"  Heures en vacances: {nb_school_holidays}")

    return df_merged


def save_to_database(df, table_name="holiday_calendar"):
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

    # Sauvegarde en base
    df.to_sql(table_name, engine, if_exists="replace", index=False)

    # Vérification
    count = pd.read_sql(f"SELECT COUNT(*) as total FROM {table_name}", engine).iloc[0][
        "total"
    ]
    print(f"  {count} enregistrements sauvegardés")


if __name__ == "__main__":
    print("=" * 50)
    print("   Chargement jours feries (fichier CSV)")
    print("=" * 50 + "\n")

    # Charger fichier CSV
    df_holidays = load_holidays_from_file("data/public_holidays_2026.csv")

    # Enrichir avec vacances scolaires
    df_holidays_enriched = enrich_with_school_holidays(df_holidays)

    print("\n=== Aperçu jours fériés ===")
    print(df_holidays_enriched.head(15))

    # Créer calendrier horaire
    df_calendar = create_hourly_calendar("2026-01-01", "2026-12-31")

    # Fusionner calendrier et jours fériés
    df_final = merge_calendar_with_holidays(df_calendar, df_holidays_enriched)

    # Sauvegarder en base
    save_to_database(df_final, "holiday_calendar")

    # Export CSV
    output_csv = "data/holiday_calendar_2026.csv"
    df_final.to_csv(output_csv, index=False)
    print(f"\nExport CSV: {output_csv}")

    print("\n" + "=" * 50)
    print("           Traitement terminé")
    print("=" * 50)
