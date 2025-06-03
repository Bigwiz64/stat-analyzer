import sqlite3
from data_pipeline.api_utils.path_utils import get_db_path

with sqlite3.connect(get_db_path()) as conn:
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(player_stats)")
for col in cursor.fetchall():
    print(col[1])

