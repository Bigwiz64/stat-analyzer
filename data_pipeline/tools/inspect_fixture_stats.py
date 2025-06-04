import sqlite3
import sys
import os
from dotenv import load_dotenv

# 🔁 Import chemins et API
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from data_pipeline.api_utils.path_utils import get_db_path

def inspect_fixture_stats(fixture_id):
    # Connexion à la base de données
    DB_PATH = get_db_path()
    print(f"📂 Base de données utilisée : {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Récupération des deux équipes et de la saison du match
        cursor.execute("""
            SELECT home_team_id, away_team_id, season
            FROM fixtures
            WHERE id = ?
        """, (fixture_id,))
        row = cursor.fetchone()

        if not row:
            print("❌ Match introuvable.")
            return

        home_team_id, away_team_id, season = row
        print(f"✅ Match {fixture_id} : {home_team_id} vs {away_team_id} | Saison : {season}")

        # Récupération des statistiques des joueurs
        cursor.execute("""
            SELECT *
            FROM player_stats
            WHERE team_id IN (?, ?) AND season = ?
        """, (home_team_id, away_team_id, season))

        players = cursor.fetchall()

        if players:
            print(f"🎯 {len(players)} joueurs trouvés.")
            for p in players:
                print(p)
        else:
            print("⚠️ Aucun joueur trouvé pour ces équipes et cette saison.")

    finally:
        conn.close()

if __name__ == "__main__":
    fixture_id = int(input("🆔 Entrez l'ID du match (fixture_id) : "))
    inspect_fixture_stats(fixture_id)
