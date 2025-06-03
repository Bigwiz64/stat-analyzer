import sqlite3
import os
from data_pipeline.api_utils.path_utils import get_db_path

# ✅ Ajuste ce chemin si tu l’as déplacé
DB_PATH = get_db_path()

if not os.path.exists(DB_PATH):
    print(f"❌ Fichier {DB_PATH} introuvable.")
    exit()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("✅ Tables trouvées dans la base :", [t[0] for t in tables])
