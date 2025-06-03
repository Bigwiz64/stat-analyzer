import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from data_pipeline.api_utils.path_utils import get_db_path
import sqlite3

db_path = get_db_path()
print(f"📁 Base utilisée : {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT id, name FROM leagues WHERE country = 'Norvège'")
results = cursor.fetchall()

print("📋 Ligues pour la Norvège :")
for row in results:
    print(f"ID: {row[0]}, Nom: {row[1]}")
