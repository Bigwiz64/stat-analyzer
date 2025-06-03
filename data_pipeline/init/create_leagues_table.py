import sqlite3
import os
from data_pipeline.api_utils.path_utils import get_db_path

DB_PATH = get_db_path()

def recreate_leagues_table():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS leagues")
        cursor.execute("""
            CREATE TABLE leagues (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                country TEXT NOT NULL
            )
        """)
        conn.commit()
        print("✅ Table 'leagues' recréée proprement.")

if __name__ == "__main__":
    recreate_leagues_table()
