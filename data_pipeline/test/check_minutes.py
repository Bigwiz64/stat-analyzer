# 📁 check_minutes.py
import sqlite3
from data_pipeline.api_utils.path_utils import get_db_path

DB_PATH = get_db_path()
fixture_id = 1224237  # ou un autre match

with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT elapsed, extra FROM fixture_events WHERE fixture_id = ?", (fixture_id,))
    rows = cursor.fetchall()

for row in rows:
    print(f"Minute : {row[0]}  |  Extra : {row[1]}")
