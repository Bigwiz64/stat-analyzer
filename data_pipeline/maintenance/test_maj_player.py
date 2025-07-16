import requests

headers = {
    "X-RapidAPI-Key": "5343ef8cf97a1d2a8e6d50fd7409cb4e",
    "X-RapidAPI-Host": "v3.football.api-sports.io"
}
params = {
    "team": 327,         # Exemple : ID de l’équipe de Kasper Høgh
    "season": 2025
}

r = requests.get("https://v3.football.api-sports.io/players", headers=headers, params=params)
print(r.json())
