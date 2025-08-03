"""
Script pour importer les matchs des saisons précédentes (10 ans) pour toutes les ligues définies.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from import_fixtures_2024 import insert_fixture, update_players_table
from data_pipeline.api_utils.utils_api import get_api_json
from data_pipeline.api_utils.path_utils import get_db_path
import sqlite3
import time

DB_PATH = get_db_path()
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ✅ Saisons à importer
PAST_SEASONS = [f"{year}-{year+1}" for year in range(2014, 2024)]
LEAGUES = [
    169
]

FROM_DATE = "2024-03-01"
TO_DATE = "2024-11-02"
API_KEY = os.getenv("API_SPORT_KEY")

def season_label_to_api(season_label):
    return int(season_label.split("-")[0])

def importer_fixtures(league_id, season_api, season_str):
    print(f"📦 Ligue {league_id} | Saison API: {season_api} | Saison Base: {season_str} | {FROM_DATE} → {TO_DATE}")
    res = get_api_json("fixtures", params={
        "league": league_id,
        "season": season_api,
        "from": FROM_DATE,
        "to": TO_DATE
    })
    fixtures = res.get("response", [])
    total_added = 0
    team_ids = set()

    for fixture in fixtures:
        insert_fixture(fixture, season_str)
        home_id = fixture.get("teams", {}).get("home", {}).get("id")
        away_id = fixture.get("teams", {}).get("away", {}).get("id")
        if home_id: team_ids.add(home_id)
        if away_id: team_ids.add(away_id)
        total_added += 1

    print(f"✅ {total_added} matchs traités pour la ligue {league_id}")
    print(f"🔁 Mise à jour des joueurs pour {len(team_ids)} équipes")
    update_players_table(list(team_ids), api_key=API_KEY, season=season_str)
    time.sleep(1.5)

if __name__ == "__main__":
    for league_id in LEAGUES:
        for season_str in PAST_SEASONS:
            season_api = season_label_to_api(season_str)
            importer_fixtures(league_id, season_api, season_str)

    conn.commit()
    print("✅ Importation complète des saisons passées terminée.")