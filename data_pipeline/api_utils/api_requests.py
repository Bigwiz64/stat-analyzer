import requests
import os

def get_api_key():
    # Récupère la clé API depuis une variable d'environnement
    return os.getenv("SPORTS_API_KEY")  # ⚡⚡ mets ta clé API dans ton fichier .env ou exporte-la

def get_fixture_stats(fixture_id):
    url = f"https://v3.football.api-sports.io/fixtures/players?fixture={fixture_id}"
    headers = {
        "x-apisports-key": get_api_key()
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_fixture_events(fixture_id):
    url = f"https://v3.football.api-sports.io/fixtures/events?fixture={fixture_id}"
    headers = {
        "x-apisports-key": get_api_key()
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()
