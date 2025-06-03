# 📁 data_pipeline/schema/create_fixture_events_table.py

import sqlite3
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from data_pipeline.api_utils.path_utils import get_db_path

DB_PATH = get_db_path()
print(f"📁 Base utilisée : {DB_PATH}")

with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()

    # 🔁 Supprimer la table existante si elle existe (proprement)
    cursor.execute("DROP TABLE IF EXISTS fixture_events")

    # ✅ Recréation complète avec la colonne `minute`
    cursor.execute("""
    CREATE TABLE fixture_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fixture_id INTEGER,
        team_id INTEGER,
        player_id INTEGER,
        assist_id INTEGER,
        type TEXT,
        detail TEXT,
        comments TEXT,
        elapsed INTEGER,
        extra INTEGER,
        minute INTEGER,
        FOREIGN KEY (fixture_id) REFERENCES fixtures(id)
    )
    """)

    conn.commit()
    print("✅ Table 'fixture_events' recréée avec succès (incluant 'minute').")
