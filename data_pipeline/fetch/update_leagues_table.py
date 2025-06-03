import sqlite3
import os
from data_pipeline.api_utils.path_utils import get_db_path

DB_PATH = get_db_path()


def add_column_if_not_exists(cursor, table, column, col_type):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        print(f"✅ Colonne '{column}' ajoutée à la table '{table}'.")
    except sqlite3.OperationalError:
        print(f"ℹ️ Colonne '{column}' déjà existante.")

def update_leagues_table():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        add_column_if_not_exists(cursor, "leagues", "logo", "TEXT")
        add_column_if_not_exists(cursor, "leagues", "flag", "TEXT")
        conn.commit()

if __name__ == "__main__":
    update_leagues_table()
