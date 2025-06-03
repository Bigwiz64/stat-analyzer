import sqlite3
import sys
import os
from collections import defaultdict

# Ajoute le dossier racine au chemin Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from data_pipeline.api_utils.path_utils import get_db_path

DB_PATH = get_db_path()

def lister_dates_par_championnat():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DATE(f.date), l.country, l.name
        FROM fixtures f
        JOIN leagues l ON f.league_id = l.id
        ORDER BY l.country, l.name, f.date
    """)
    data = cursor.fetchall()
    conn.close()

    calendrier = defaultdict(lambda: defaultdict(list))

    for match_date, country, league in data:
        calendrier[country][league].append(match_date)

    for country in sorted(calendrier):
        print(f"\n🌍 {country}")
        for league in sorted(calendrier[country]):
            dates = calendrier[country][league]
            print(f"  📅 {league} ({len(dates)} dates) → {', '.join(sorted(set(dates)))}")

if __name__ == "__main__":
    print("📆 Analyse des dates par championnat en cours...")
    lister_dates_par_championnat()
