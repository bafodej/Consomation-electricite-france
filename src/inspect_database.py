"""
Script pour inspecter la base de donnees SQLite
Sans besoin de SGBD externe
"""

import os
import sqlite3

import pandas as pd


def inspect_database(db_path="database/rte_consommation.db"):
    """
    Inspecte et affiche les informations de la base de donnees

    Args:
        db_path: Chemin vers la base SQLite
    """
    if not os.path.exists(db_path):
        print(f"Base de donnees introuvable: {db_path}")
        return

    print("=" * 70)
    print(f"   Inspection base de donnees: {db_path}")
    print("=" * 70 + "\n")

    # Connexion
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Lister toutes les tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print(f"Nombre de tables: {len(tables)}\n")

    # Pour chaque table
    for (table_name,) in tables:
        print("=" * 70)
        print(f"TABLE: {table_name}")
        print("=" * 70)

        # Structure de la table
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()

        print("\nSTRUCTURE:")
        print(f"{'Colonne':<25} {'Type':<15} {'Not Null':<10} {'PK'}")
        print("-" * 70)
        for col in columns:
            col_id, name, col_type, notnull, default, pk = col
            print(
                f"{name:<25} {col_type:<15} {'YES' if notnull else 'NO':<10} {'YES' if pk else 'NO'}"
            )

        # Nombre de lignes
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"\nNOMBRE DE LIGNES: {count}")

        # Apercu des donnees (5 premieres lignes)
        print("\nAPERCU (5 premieres lignes):")
        df = pd.read_sql(f"SELECT * FROM {table_name} LIMIT 5", conn)
        print(df.to_string(index=False))

        # Statistiques pour tables numeriques
        if table_name in ["consommation", "prix_spot_electricite", "meteo"]:
            print("\nSTATISTIQUES:")
            if table_name == "consommation":
                stats = pd.read_sql(
                    f"""
                    SELECT
                        MIN(datetime) as date_debut,
                        MAX(datetime) as date_fin,
                        ROUND(AVG(mw_conso), 2) as conso_moyenne,
                        ROUND(MIN(mw_conso), 2) as conso_min,
                        ROUND(MAX(mw_conso), 2) as conso_max
                    FROM {table_name}
                """,
                    conn,
                )
            elif table_name == "prix_spot_electricite":
                stats = pd.read_sql(
                    f"""
                    SELECT
                        MIN(datetime) as date_debut,
                        MAX(datetime) as date_fin,
                        ROUND(AVG(prix_spot_eur_mwh), 2) as prix_moyen,
                        ROUND(MIN(prix_spot_eur_mwh), 2) as prix_min,
                        ROUND(MAX(prix_spot_eur_mwh), 2) as prix_max
                    FROM {table_name}
                """,
                    conn,
                )
            elif table_name == "meteo":
                stats = pd.read_sql(
                    f"""
                    SELECT
                        MIN(datetime) as date_debut,
                        MAX(datetime) as date_fin,
                        ROUND(AVG(temperature), 2) as temp_moyenne,
                        ROUND(AVG(vent), 2) as vent_moyen
                    FROM {table_name}
                """,
                    conn,
                )

            print(stats.to_string(index=False))

        print("\n")

    # Taille du fichier
    file_size = os.path.getsize(db_path)
    size_mb = file_size / (1024 * 1024)
    print("=" * 70)
    print(f"TAILLE FICHIER: {size_mb:.2f} MB ({file_size:,} bytes)")
    print("=" * 70)

    conn.close()


def export_table_to_csv(table_name, output_file=None):
    """
    Exporte une table en CSV pour inspection

    Args:
        table_name: Nom de la table
        output_file: Fichier de sortie (optionnel)
    """
    db_path = "database/rte_consommation.db"

    if not os.path.exists(db_path):
        print(f"Base de donnees introuvable: {db_path}")
        return

    conn = sqlite3.connect(db_path)

    # Lire la table
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)

    # Nom fichier par defaut
    if output_file is None:
        output_file = f"data/export_{table_name}.csv"

    # Exporter
    df.to_csv(output_file, index=False)
    print(f"Table '{table_name}' exportee vers: {output_file}")
    print(f"Lignes: {len(df)}, Colonnes: {len(df.columns)}")

    conn.close()


def query_custom(sql_query):
    """
    Execute une requete SQL personnalisee

    Args:
        sql_query: Requete SQL
    """
    db_path = "database/rte_consommation.db"

    if not os.path.exists(db_path):
        print(f"Base de donnees introuvable: {db_path}")
        return

    conn = sqlite3.connect(db_path)

    try:
        df = pd.read_sql(sql_query, conn)
        print("\nResultat de la requete:")
        print(df.to_string(index=False))
        print(f"\nNombre de lignes: {len(df)}")
    except Exception as e:
        print(f"Erreur SQL: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    print("\n")

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "export" and len(sys.argv) > 2:
            table_name = sys.argv[2]
            export_table_to_csv(table_name)

        elif command == "query" and len(sys.argv) > 2:
            sql_query = " ".join(sys.argv[2:])
            query_custom(sql_query)

        else:
            print("Usage:")
            print("  python src/inspect_database.py                    # Inspecter toute la base")
            print(
                "  python src/inspect_database.py export consommation  # Exporter une table"
            )
            print(
                "  python src/inspect_database.py query 'SELECT ...'   # Requete personnalisee"
            )
    else:
        # Inspection complete par defaut
        inspect_database()
