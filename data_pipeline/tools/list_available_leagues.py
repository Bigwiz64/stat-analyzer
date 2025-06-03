import sqlite3
import sys
import os
from collections import defaultdict

# Ajoute le dossier racine au chemin Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from data_pipeline.api_utils.path_utils import get_db_path

DB_PATH = get_db_path()

with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT id, name, country FROM leagues ORDER BY country, name")
    leagues = cursor.fetchall()

print("🌍 Ligues disponibles :")
for league in leagues:
    print(f"  - {league[2]} / {league[1]} (ID: {league[0]})")
