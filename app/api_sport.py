import requests
import os
from datetime import datetime

API_KEY = os.getenv("API_SPORT_KEY")

def get_today_football_matches():
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {
        "x-apisports-key": API_KEY
    }

    today = datetime.now().strftime("%Y-%m-%d")

    params = {
        "date": today,
        "timezone": "Europe/Paris"
    }

    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json().get("response", [])
    else:
        print("Erreur API:", response.status_code, response.text)
        return []

def get_players_for_match(fixture_id):
    url = "https://v3.football.api-sports.io/players"
    headers = {
        "x-apisports-key": API_KEY
    }
    params = {
        "fixture": fixture_id
    }

    response = requests.get(url, headers=headers, params=params)

    print("====== API RESPONSE PLAYERS ======")
    print(response.status_code)
    print(response.json())

    if response.status_code == 200:
        return response.json().get("response", [])
    else:
        return []

def get_lineups_for_match(fixture_id):
    url = "https://v3.football.api-sports.io/fixtures/lineups"
    headers = {
        "x-apisports-key": API_KEY
    }
    params = {
        "fixture": fixture_id
    }

    response = requests.get(url, headers=headers, params=params)

    print("====== API RESPONSE LINEUPS ======")
    print(response.status_code)
    print(response.json())

    if response.status_code == 200:
        return response.json().get("response", [])
    else:
        return []

def get_team_squad(team_id):
    url = "https://v3.football.api-sports.io/players/squads"
    headers = {
        "x-apisports-key": API_KEY
    }
    params = {
        "team": team_id
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json().get("response", [])
        if data:
            return data[0].get("players", [])
    else:
        print("Erreur API (squad):", response.status_code, response.text)

    return []


def get_match_by_id(fixture_id):
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {
        "x-apisports-key": API_KEY
    }
    params = {
        "id": fixture_id
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json().get("response", [])
        return data[0] if data else None
    else:
        return None

def get_player_stats_last_matches(player_id, season=2023):
    url = "https://v3.football.api-sports.io/players"
    headers = {
        "x-apisports-key": API_KEY
    }
    params = {
        "id": player_id,
        "season": season
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json().get("response", [])
        if data:
            # On prend uniquement les 5 derniers matchs
            return data[0].get("statistics", [])[:5]
    return []
