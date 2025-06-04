import requests
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("API_SPORT_KEY")
fixture_id = 1342714

url = f"https://v3.football.api-sports.io/fixtures/players?fixture={fixture_id}"
headers = {"x-apisports-key": API_KEY}

response = requests.get(url, headers=headers)
data = response.json()

print("🔍 Nombre de joueurs retournés :", len(data.get("response", [])))
print("Contenu brut de la réponse :")
print(data)

