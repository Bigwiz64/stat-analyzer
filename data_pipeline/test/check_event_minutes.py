import sys
import os
import sqlite3

# Ajoute le chemin racine pour les imports personnalisés
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from data_pipeline.api_utils.path_utils import get_db_path

# ID du match à vérifier
FIXTURE_ID = 1224237
DB_PATH = get_db_path()

# Connexion DB
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    SELECT minute, elapsed, extra, type, detail, player_id 
    FROM fixture_events 
    WHERE fixture_id = ? 
    ORDER BY elapsed, extra
""", (FIXTURE_ID,))
rows = cursor.fetchall()

print(f"\n📋 Événements pour le match {FIXTURE_ID} :\n")
for minute, elapsed, extra, etype, detail, player_id in rows:
    min_display = f"{minute}'" if minute else "??"
    print(f"{min_display:>4} | {etype:<8} – {detail:<20} | player_id: {player_id or '?'} | elapsed: {elapsed}, extra: {extra}")

conn.close()
