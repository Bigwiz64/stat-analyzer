import os
import json
from dotenv import load_dotenv

# 🔁 Accès aux fonctions existantes
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from data_pipeline.api_utils.utils_api import get_api_json

# 🔐 Charge les variables d’environnement (.env)
load_dotenv()

# 🆔 ID du match à inspecter
fixture_id = 1224237

# 📡 Appel à l'API Sport pour les événements de ce match
response = get_api_json("fixtures/events", params={"fixture": fixture_id})
events = response.get("response", [])

# 🖨️ Affiche le contenu brut (bien indenté)
print(f"🎯 {len(events)} événements récupérés pour le match {fixture_id} :\n")
print(json.dumps(events, indent=2))
