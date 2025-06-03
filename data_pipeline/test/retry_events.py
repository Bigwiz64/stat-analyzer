import sqlite3
from dotenv import load_dotenv
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from data_pipeline.api_utils.utils_api import get_api_json
from data_pipeline.api_utils.path_utils import get_db_path

# 🔐 Charger les variables d'environnement
load_dotenv()

# 📁 Connexion à la base
DB_PATH = get_db_path()
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 🎯 Match à forcer
FIXTURE_ID = 1213908

def retry_fixture_events(fixture_id):
    print(f"🔄 Rechargement des événements pour le match {fixture_id}")
    
    # Supprimer les anciens événements (optionnel mais conseillé pour corriger)
    cursor.execute("DELETE FROM fixture_events WHERE fixture_id = ?", (fixture_id,))
    
    try:
        events_data = get_api_json("fixtures/events", params={"fixture": fixture_id}).get("response", [])
        print(f"📦 {len(events_data)} événements récupérés pour {fixture_id}")

        for event in events_data:
            elapsed = event.get("time", {}).get("elapsed")
            extra = event.get("time", {}).get("extra") or 0

            if elapsed is None:
                print(f"⚠️ Pas de 'elapsed' : {event}")
                minute = None
            else:
                minute = elapsed + extra

            team_id = event["team"]["id"]
            player = event.get("player")
            assist = event.get("assist")
            player_id = player["id"] if player else None
            assist_id = assist["id"] if assist else None

            cursor.execute("""
                INSERT INTO fixture_events (
                    fixture_id, team_id, player_id, assist_id, type, detail, comments, elapsed, extra, minute
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fixture_id,
                team_id,
                player_id,
                assist_id,
                event["type"],
                event["detail"],
                event.get("comments"),
                elapsed,
                extra,
                minute
            ))

        conn.commit()
        print("✅ Événements insérés avec succès.")
    
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    retry_fixture_events(FIXTURE_ID)
