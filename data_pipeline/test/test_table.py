import sqlite3
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "db", "data.db"))
fixture_id = 1224237

with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(fixture_events)")
    print("🧱 Colonnes de la table :")
    for col in cursor.fetchall():
        print(col)

    print("\n📋 Données brutes des événements :")
    cursor.execute("SELECT * FROM fixture_events WHERE fixture_id = ?", (fixture_id,))
    for row in cursor.fetchall():
        print(row)
