import sys
import os
import sqlite3

# Ajout du chemin racine du projet pour les imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from data_pipeline.api_utils.utils_api import get_api_json
from data_pipeline.api_utils.path_utils import get_db_path

# === PARAMÈTRES ===
FIXTURE_ID = 1224237  # à modifier au besoin
DB_PATH = get_db_path()

# === Connexion DB ===
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# === Suppression des anciens événements ===
cursor.execute("DELETE FROM fixture_events WHERE fixture_id = ?", (FIXTURE_ID,))
print(f"🗑️ Événements supprimés pour le match {FIXTURE_ID}")

# === Récupération depuis l’API ===
events_data = get_api_json("fixtures/events", params={"fixture": FIXTURE_ID}).get("response", [])

# === Insertion ===
inserted = 0
for event in events_data:
    elapsed = event["time"].get("elapsed", 0) or 0
    extra = event["time"].get("extra", 0) or 0
    minute = elapsed + extra

    cursor.execute("""
        INSERT OR IGNORE INTO fixture_events (
            fixture_id, team_id, player_id, assist_id, type, detail, comments, elapsed, extra, minute
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        FIXTURE_ID,
        event["team"]["id"],
        event["player"]["id"] if event.get("player") else None,
        event["assist"]["id"] if event.get("assist") else None,
        event["type"],
        event["detail"],
        event.get("comments"),
        elapsed,
        extra,
        minute
    ))
    inserted += 1

conn.commit()
conn.close()

print(f"✅ {inserted} événements importés pour le match {FIXTURE_ID}")
