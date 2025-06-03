import sqlite3
import os
import sys
# 🔁 Import chemins et API
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from data_pipeline.api_utils.utils_api import get_api_json
from data_pipeline.api_utils.path_utils import get_db_path

DB_PATH = get_db_path()

def clean_duplicates_keep_any():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        print("🧹 Nettoyage simple : on garde 1 ligne par (player_id, fixture_id)...")

        cursor.execute("""
            CREATE TEMP TABLE best_rows AS
            SELECT MIN(rowid) AS rowid
            FROM player_stats
            GROUP BY player_id, fixture_id
        """)

        cursor.execute("""
            DELETE FROM player_stats
            WHERE rowid NOT IN (SELECT rowid FROM best_rows)
        """)

        conn.commit()
        print("✅ Terminé. Une ligne conservée par joueur et match.")

if __name__ == "__main__":
    clean_duplicates_keep_any()