import requests
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("API_SPORT_KEY")
headers = {"x-apisports-key": API_KEY}

res = requests.get(
    "https://v3.football.api-sports.io/fixtures",
    headers=headers,
    params={
        "league": 61,
        "season": 2024,
        "page": 1
    }
)

data = res.json()
print("➡️ Résultat brut :", data)
print("📊 Nombre de matchs :", len(data.get("response", [])))
