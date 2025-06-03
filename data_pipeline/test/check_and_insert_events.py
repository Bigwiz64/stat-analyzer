import os
import sys
import sqlite3

# 🔁 Ajout du chemin projet
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from data_pipeline.api_utils.utils_api import get_api_json
from data_pipeline.api_utils.path_utils import get_db_path

DB_PATH = get_db_path()
FIXTURE_ID = 1224237  # 🏟️ Match ciblé

def insert_fixture_events(fixture_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM fixture_events WHERE fixture_id = ?", (fixture_id,))
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"⏭️ Les événements pour le match {fixture_id} sont déjà en base ({count} événements).")
            return

        try:
            events_data = get_api_json("fixtures/events", params={"fixture": fixture_id}).get("response", [])
            total = 0
            for event in events_data:
                cursor.execute("""
                    INSERT OR IGNORE INTO fixture_events (
                        fixture_id, team_id, player_id, assist_id, type, detail, comments, elapsed, extra
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fixture_id,
                    event["team"]["id"],
                    event["player"]["id"] if event["player"] else None,
                    event["assist"]["id"] if event.get("assist") else None,
                    event["type"],
                    event["detail"],
                    event.get("comments"),
                    event["time"]["elapsed"],
                    event["time"].get("extra")
                ))
                total += 1
            conn.commit()
            print(f"✅ {total} événement(s) inséré(s) pour le match {fixture_id}.")
        except Exception as e:
            print(f"❌ Erreur lors de l'insertion des événements pour le match {fixture_id} : {e}")

# 🚀 Lancement
if __name__ == "__main__":
    insert_fixture_events(FIXTURE_ID)
