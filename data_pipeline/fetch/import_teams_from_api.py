import sqlite3
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from dotenv import load_dotenv
from data_pipeline.api_utils.path_utils import get_db_path
from data_pipeline.api_utils.utils_api import get_api_json

# Chargement de la base de données et des variables d'environnement
load_dotenv()
DB_PATH = get_db_path()

# Saison par défaut
DEFAULT_SEASON = 2024

# Liste d'IDs de ligues à traiter (doit correspondre à celles déjà présentes dans la table leagues)
LEAGUE_IDS = [
    2, 3, 848, 61, 62, 39, 40, 140, 141, 78, 79, 81, 135, 136,
    88, 94, 95, 203, 179, 218, 259, 144, 172, 244, 103, 113, 119,
    186, 307, 128, 71, 265, 169, 318, 239, 292, 210, 106, 283, 207, 333
]

# Ajout de colonne si manquante
def add_column_if_not_exists(cursor, table, column, col_type):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        print(f"✅ Colonne '{column}' ajoutée à la table '{table}'.")
    except sqlite3.OperationalError:
        print(f"ℹ️ Colonne '{column}' déjà existante ou erreur ignorée.")

# Création de la table teams si elle n'existe pas
def create_teams_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY,
            name TEXT,
            country TEXT,
            logo TEXT
        )
    """)
    add_column_if_not_exists(cursor, "teams", "league_id", "INTEGER")
    print("✅ Table 'teams' vérifiée/créée.")

# Insertion des équipes pour chaque ligue
def insert_teams_for_league(cursor, league_id, season):
    print(f"\n📥 Traitement de la ligue ID {league_id} pour la saison {season}...")
    response = get_api_json("teams", params={"league": league_id, "season": season})

    for entry in response.get("response", []):
        team = entry["team"]
        team_id = team["id"]
        name = team["name"]
        country = team["country"]
        logo = team["logo"]

        cursor.execute("SELECT 1 FROM teams WHERE id = ?", (team_id,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO teams (id, name, country, logo, league_id)
                VALUES (?, ?, ?, ?, ?)
            """, (team_id, name, country, logo, league_id))
            print(f"✅ Ajouté : {team_id} | {name} ({country})")
        else:
            print(f"ℹ️ Déjà présent : {team_id} | {name}")

# Programme principal
def main():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        create_teams_table(cursor)
        for league_id in LEAGUE_IDS:
            insert_teams_for_league(cursor, league_id, DEFAULT_SEASON)
        conn.commit()
        print("\n🎉 Importation des équipes terminée.")

if __name__ == "__main__":
    main()
