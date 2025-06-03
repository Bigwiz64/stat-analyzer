import os

def get_db_path():
    # Remonte à la racine du projet
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    # Va chercher la base de données dans le bon dossier
    db_path = os.path.join(base_dir, "data_pipeline", "db", "data.db")
    return db_path


