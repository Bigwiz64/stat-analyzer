import sqlite3
import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from data_pipeline.api_utils.path_utils import get_db_path

db_path = get_db_path()
conn = sqlite3.connect(db_path)

query = """
SELECT fe.*, p.name as player_name, a.name as assist_name
FROM fixture_events fe
LEFT JOIN players p ON fe.player_id = p.id
LEFT JOIN players a ON fe.assist_id = a.id
WHERE fe.type = 'Goal' AND (fe.assist_id IS NULL OR fe.player_id = fe.assist_id)
"""

df = pd.read_sql_query(query, conn)
df.to_csv("data_pipeline/outputs/evenements_suspects.csv", index=False)
conn.close()

print("📄 Fichier exporté : data_pipeline/outputs/evenements_suspects.csv")
