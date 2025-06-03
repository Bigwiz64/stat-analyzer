import os

def run_script(script_path):
    os.system(f"python data_pipeline/{script_path}")

def run_script_with_dates(script_path):
    from_date = input("📅 Date de début (YYYY-MM-DD) : ").strip()
    to_date = input("📅 Date de fin (YYYY-MM-DD) : ").strip()
    os.system(f"python data_pipeline/{script_path} {from_date} {to_date}")

def run_script_with_season_and_dates(script_path):
    season = input("🎯 Saison (ex: 2024) : ").strip()
    from_date = input("📅 Date de début (YYYY-MM-DD) : ").strip()
    to_date = input("📅 Date de fin (YYYY-MM-DD) : ").strip()
    os.system(f"python data_pipeline/{script_path} {season} {from_date} {to_date}")

def run_script_for_one_league(script_path):
    league_id = input("🏟️ ID de la ligue : ").strip()
    season = input("🎯 Saison (ex: 2024) : ").strip()
    from_date = input("📅 Date de début (YYYY-MM-DD) : ").strip()
    to_date = input("📅 Date de fin (YYYY-MM-DD) : ").strip()
    os.system(f"python data_pipeline/{script_path} {league_id} {season} {from_date} {to_date}")


def menu():
    while True:
        print("\n====== MENU PEAKSTAT - MAJ DONNÉES ======")
        print("1. 📥 Importer les matchs (import_fixtures_2024.py)")
        print("2. 🔁 Mettre à jour les scores (update_scores.py)")
        print("3. 📊 Charger une saison complète (load_season_2024.py)")
        print("4. 🧼 Supprimer doublons (clean_duplicates2.py)")
        print("5. 📦 Recharger logos équipes (update_team_logos.py)")
        print("6. 🛠️ Vérifier saisons ligues (check_seasons.py)")
        print("7. ➕ Insérer les ligues manquantes (insert_missing_leagues.py)")
        print("8. 🎯 Importer une ligue précise (fetch_one_league.py)")
        print("9. 📄 Lister les ligues disponibles")
        print("0. ❌ Quitter")
        
        choice = input("👉 Que veux-tu faire ? ")

        if choice == "1":
            run_script_with_dates("fetch/import_fixtures_2024.py")
        elif choice == "2":
            run_script("update_scores.py")
        elif choice == "3":
            run_script_with_season_and_dates("fetch/load_season_2024.py")
        elif choice == "4":
            run_script("tools/clean_duplicates2.py")
        elif choice == "5":
            run_script("tools/update_team_logos.py")
        elif choice == "6":
            run_script("tools/check_seasons.py")
        elif choice == "7":
            run_script("tools/insert_missing_leagues.py")
        elif choice == "8":
            run_script_for_one_league("fetch/fetch_one_league.py")
        elif choice == "9":
            run_script("tools/list_available_leagues.py")
        elif choice == "0":
            print("👋 À bientôt !")
            break
        else:
            print("❌ Choix invalide, réessaie.")

if __name__ == "__main__":
    menu()
