"""
Script d'import des donnees SQLite vers PostgreSQL
Migre les donnees de consommation electrique
"""

import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def get_sqlite_engine():
    """Connexion SQLite"""
    db_path = os.path.abspath('database/rte_consommation.db')
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Base SQLite introuvable: {db_path}")
    return create_engine(f'sqlite:///{db_path}')

def get_postgres_engine():
    """Connexion PostgreSQL"""
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5432')
    db = os.getenv('POSTGRES_DB', 'rte_consommation')
    user = os.getenv('POSTGRES_USER', 'rte_user')
    password = os.getenv('POSTGRES_PASSWORD', 'rte_secure_password')

    conn_string = f'postgresql://{user}:{password}@{host}:{port}/{db}'
    return create_engine(conn_string)

def import_consommation():
    """Importe les donnees de consommation"""
    print("Lecture des donnees SQLite...")
    sqlite_engine = get_sqlite_engine()

    df = pd.read_sql_table('consommation', sqlite_engine)
    print(f"  {len(df)} lignes trouvees")

    if 'source' not in df.columns:
        df['source'] = 'SYNTHETIC'
    if 'region' not in df.columns:
        df['region'] = 'France'
    if 'created_at' not in df.columns:
        df['created_at'] = pd.Timestamp.now()

    print("Connexion a PostgreSQL...")
    postgres_engine = get_postgres_engine()

    print("Import des donnees...")
    df.to_sql(
        'consommation',
        postgres_engine,
        if_exists='append',
        index=False,
        method='multi',
        chunksize=100
    )

    print("Import termine avec succes")

    result = pd.read_sql_query(
        'SELECT COUNT(*) as total FROM consommation',
        postgres_engine
    )
    print(f"Total en base PostgreSQL: {result['total'][0]} lignes")

def import_previsions():
    """Importe les previsions si elles existent"""
    try:
        print("\nRecherche de previsions...")
        sqlite_engine = get_sqlite_engine()

        df = pd.read_sql_table('prevision', sqlite_engine)
        if len(df) > 0:
            print(f"  {len(df)} previsions trouvees")
            postgres_engine = get_postgres_engine()
            df.to_sql(
                'prevision',
                postgres_engine,
                if_exists='append',
                index=False,
                method='multi',
                chunksize=100
            )
            print("Previsions importees")
        else:
            print("  Aucune prevision a importer")
    except Exception as e:
        print(f"  Table prevision non trouvee ou vide: {e}")

def verify_import():
    """Verifie l'integrite des donnees importees"""
    print("\nVerification de l'import...")
    postgres_engine = get_postgres_engine()

    stats = pd.read_sql_query("""
        SELECT
            COUNT(*) as total_mesures,
            MIN(datetime) as premiere_mesure,
            MAX(datetime) as derniere_mesure,
            ROUND(AVG(mw_conso), 2) as conso_moyenne,
            ROUND(MIN(mw_conso), 2) as conso_min,
            ROUND(MAX(mw_conso), 2) as conso_max
        FROM consommation
    """, postgres_engine)

    print("\nStatistiques PostgreSQL:")
    print(f"  Total mesures: {stats['total_mesures'][0]}")
    print(f"  Periode: {stats['premiere_mesure'][0]} -> {stats['derniere_mesure'][0]}")
    print(f"  Consommation moyenne: {stats['conso_moyenne'][0]} MW")
    print(f"  Consommation min: {stats['conso_min'][0]} MW")
    print(f"  Consommation max: {stats['conso_max'][0]} MW")

    duplicates = pd.read_sql_query("""
        SELECT datetime, COUNT(*) as nb
        FROM consommation
        GROUP BY datetime
        HAVING COUNT(*) > 1
    """, postgres_engine)

    if len(duplicates) > 0:
        print(f"\n  ATTENTION: {len(duplicates)} doublons detectes")
    else:
        print("\n  Aucun doublon detecte")

if __name__ == '__main__':
    try:
        print("=== Import SQLite -> PostgreSQL ===\n")
        import_consommation()
        import_previsions()
        verify_import()
        print("\n=== Import termine ===")
    except Exception as e:
        print(f"\nERREUR: {e}")
        exit(1)
