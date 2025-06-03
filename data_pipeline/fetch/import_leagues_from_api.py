# Créer la table League dans la DB 

import sqlite3
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from data_pipeline.api_utils.path_utils import get_db_path

# Connexion à la base
DB_PATH = get_db_path()

# Liste des ligues à insérer (ID, nom, pays, logo, drapeau)
LEAGUES_TO_INSERT = [
    (2, "UEFA Champions League", "Europe", "", ""),
    (3, "UEFA Europa League", "Europe", "", ""),
    (848, "UEFA Europa Conference League", "Europe", "", ""),
    (61, "Ligue 1", "France", "", ""),
    (62, "Ligue 2", "France", "", ""),
    (39, "Premier League", "England", "", ""),
    (40, "Championship", "England", "", ""),
    (140, "La Liga", "Spain", "", ""),
    (141, "LaLiga2", "Spain", "", ""),
    (78, "Bundesliga", "Germany", "", ""),
    (79, "2. Bundesliga", "Germany", "", ""),
    (81, "DFB Pokal", "Germany", "", ""),
    (135, "Serie A", "Italy", "", ""),
    (136, "Serie B", "Italy", "", ""),
    (88, "Eredivisie", "Netherlands", "", ""),
    (94, "Primeira Liga", "Portugal", "", ""),
    (95, "Liga Portugal 2", "Portugal", "", ""),
    (203, "Süper Lig", "Turkey", "", ""),
    (179, "Premiership", "Scotland", "", ""),
    (218, "Bundesliga Autriche", "Austria", "", ""),
    (259, "A-League", "Australia", "", ""),
    (144, "Jupiler Pro League", "Belgium", "", ""),
    (172, "First League", "Bulgaria", "", ""),
    (244, "Veikkausliiga", "Finland", "", ""),
    (103, "Eliteserien", "Norway", "", ""),
    (113, "Allsvenskan", "Sweden", "", ""),
    (119, "Superligaen", "Denmark", "", ""),
    (186, "Ligue 1", "Algeria", "", ""),
    (307, "Pro League", "Saudi Arabia", "", ""),
    (128, "Liga Profesional Argentina", "Argentina", "", ""),
    (71, "Serie A", "Brazil", "", ""),
    (265, "Primera Division", "Chile", "", ""),
    (169, "Super League", "China", "", ""),
    (318, "1. Division", "Cyprus", "", ""),
    (239, "Primera A", "Colombia", "", ""),
    (292, "K League 1", "South Korea", "", ""),
    (210, "HNL", "Croatia", "", ""),
    (106, "Ekstraklasa", "Poland", "", ""),
    (283, "Liga I", "Romania", "", ""),
    (207, "Super League", "Switzerland", "", ""),
    (333, "Premier League", "Ukraine", "", "")
]

def create_leagues_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leagues (
            id INTEGER PRIMARY KEY,
            name TEXT,
            country TEXT,
            logo TEXT,
            flag TEXT
        )
    """)
    print("✅ Table 'leagues' créée (si elle n'existait pas déjà).")

def insert_leagues(cursor):
    for league_id, name, country, logo, flag in LEAGUES_TO_INSERT:
        cursor.execute("SELECT 1 FROM leagues WHERE id = ?", (league_id,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO leagues (id, name, country, logo, flag)
                VALUES (?, ?, ?, ?, ?)
            """, (league_id, name, country, logo, flag))
            print(f"✅ Ajouté : {league_id} | {name} ({country})")
        else:
            print(f"ℹ️ Déjà présent : {league_id} | {name}")

def main():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        create_leagues_table(cursor)
        insert_leagues(cursor)
        conn.commit()

if __name__ == "__main__":
    main()
