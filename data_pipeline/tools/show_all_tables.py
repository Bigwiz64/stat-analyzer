# 📁 Fichier : data_pipeline/tools/show_all_tables.py

import sqlite3
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# 📁 Fichier : data_pipeline/tools/show_table_columns.py
from data_pipeline.api_utils.path_utils import get_db_path

DB_PATH = get_db_path()
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print(f"📂 Base de données : {DB_PATH}")
print("📋 Colonnes des tables :\n")

# Récupère toutes les tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

for (table_name,) in tables:
    print(f"🔸 Table : {table_name}")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        col_id, col_name, col_type, *_ = col
        print(f"   - {col_name} ({col_type})")
    print()

conn.close()

