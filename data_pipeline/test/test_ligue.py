import requests
from dotenv import load_dotenv
import os

# Charger les variables d’environnement
load_dotenv()
API_KEY = os.getenv("API_SPORT_KEY")
HEADERS = {"x-apisports-key": API_KEY}

def test_fixture_api(league_id, season=2024, from_date="2024-07-01", to_date="2025-06-30"):
    print(f"📦 Test pour la Ligue {league_id} - Saison {season}")
    url = "https://v3.football.api-sports.io/fixtures"
    params = {
        "league": league_id,
        "season": season,
        "from": from_date,
        "to": to_date
    }

    res = requests.get(url, headers=HEADERS, params=params)
    data = res.json()

    if data.get("errors"):
        print("❌ Erreurs :", data["errors"])
        return

    fixtures = data.get("response", [])
    print(f"✅ {len(fixtures)} matchs trouvés")

    for match in fixtures[:5]:  # On affiche les 5 premiers pour vérifier
        fixture = match["fixture"]
        teams = match["teams"]
        print(f"📅 {fixture['date']} – {teams['home']['name']} vs {teams['away']['name']}")
    
    if not fixtures:
        print("⚠️ Aucun match retourné.")

# Exemple d’appel :
if __name__ == "__main__":
    test_fixture_api(79)  # Remplace par une autre ligue si besoin
