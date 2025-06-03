import sys
import os
import sqlite3

# 🔁 Ajoute le chemin pour accéder au bon module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from data_pipeline.api_utils.path_utils import get_db_path

# 📥 Identifiant du match à tester (change-le si besoin)
fixture_id = 1224237

# 🔌 Connexion base de données
db_path = get_db_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 🔍 Récupération des événements
cursor.execute("""
    SELECT minute, type, detail, comments, player_id
    FROM fixture_events
    WHERE fixture_id = ?
    ORDER BY minute ASC
""", (fixture_id,))
events = cursor.fetchall()

# 📋 Affichage
print(f"📊 Événements pour le match {fixture_id} :\n")
for ev in events:
    minute, type_, detail, comments, player_id = ev
    print(f"{minute or '??'}' | {type_} – {detail} | player_id: {player_id} | {comments or ''}")

if not events:
    print("⚠️ Aucun événement trouvé.")

conn.close()
