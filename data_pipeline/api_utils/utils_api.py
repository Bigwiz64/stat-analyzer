import os
import time
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

# 📦 Charger .env
load_dotenv()
API_KEY = os.getenv("API_SPORT_KEY")
BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_KEY
}


def get_api_json(endpoint, params=None, pause=0.3):
    """
    Requête vers l'API avec gestion des erreurs et délai entre les appels.
    """
    url = f"{BASE_URL}/{endpoint}"
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("errors"):
            print(f"❌ Erreur API : {data['errors']}")
            return {}

        time.sleep(pause)
        return data
    except requests.exceptions.HTTPError as err:
        print(f"❌ Erreur HTTP : {err}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion : {e}")
    return {}


def convert_utc_to_local(utc_datetime_str):
    """
    Convertit un datetime UTC en heure locale française (UTC+2)
    """
    try:
        utc_dt = datetime.strptime(utc_datetime_str, "%Y-%m-%dT%H:%M:%S%z")
        local_dt = utc_dt + timedelta(hours=2)
        return local_dt.strftime("%Y-%m-%dT%H:%M:%S")
    except Exception as e:
        print(f"⚠️ Erreur de conversion date : {e}")
        return utc_datetime_str


# 🎯 Fonctions spécifiques à l'API Sport

def get_fixtures_by_league_and_season(league_id, season):
    return get_api_json("fixtures", {
        "league": league_id,
        "season": season
    })


def get_fixture_by_id(fixture_id):
    return get_api_json("fixtures", {
        "id": fixture_id
    })


def get_players_by_fixture(fixture_id):
    return get_api_json("players", {
        "fixture": fixture_id
    })


def get_leagues():
    return get_api_json("leagues")
