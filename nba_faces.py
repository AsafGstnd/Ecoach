# import pandas as pd
# import requests
# import shutil
# import os
# from nba_api.stats.static import players
#
#
# def get_players_from_csv(csv_filename):
#     """
#     Reads the CSV, cleans column names (removing '▲'), and returns unique player names.
#     """
#     try:
#         df = pd.read_csv(csv_filename)
#
#         # Clean column names (Same logic as your app.py to ensure 'Player' is found)
#         df.columns = [c.strip().replace('▲', '') for c in df.columns]
#
#         if 'Player' not in df.columns:
#             print(f"❌ Error: 'Player' column not found in {csv_filename}")
#             print(f"   Found columns: {list(df.columns)}")
#             return []
#
#         # Get unique names and drop empty ones
#         player_list = df['Player'].dropna().unique().tolist()
#         return [str(p).strip() for p in player_list if str(p).strip()]
#
#     except Exception as e:
#         print(f"❌ Error reading CSV file: {e}")
#         return []
#
#
# def get_player_headshot(player_name, all_nba_players, output_folder='player_imgs'):
#     """
#     Finds player ID and downloads their headshot.
#     """
#     if not os.path.exists(output_folder):
#         os.makedirs(output_folder)
#
#     # Find the player ID (Case-insensitive match)
#     found_player = [
#         p for p in all_nba_players
#         if p['full_name'].lower() == player_name.lower()
#     ]
#
#     if not found_player:
#         print(f"❌ Could not find ID for: {player_name}")
#         return
#
#     player_id = found_player[0]['id']
#
#     # Construct URL
#     url = f'https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{player_id}.png'
#     filename = f"{output_folder}/{player_name}.png"
#
#     # Check if file exists to save time/bandwidth
#     if os.path.exists(filename):
#         print(f"⏩ Skipping {player_name} (Already exists)")
#         return
#
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
#     }
#
#     try:
#         r = requests.get(url, stream=True, headers=headers)
#         if r.status_code == 200:
#             with open(filename, 'wb') as f:
#                 r.raw.decode_content = True
#                 shutil.copyfileobj(r.raw, f)
#             print(f"✅ Saved: {filename}")
#         else:
#             print(f"⚠️ Image not found for {player_name} (ID: {player_id})")
#     except Exception as e:
#         print(f"❌ Error downloading {player_name}: {e}")
#
#
# if __name__ == '__main__':
#     # 1. Fetch the master list of players from NBA API once
#     print("--- Fetching NBA Player Database ---")
#     all_nba_players = players.get_players()
#
#     # 2. Extract names from the CSV
#     csv_file = "player_stats.csv"
#     print(f"--- Reading names from {csv_file} ---")
#     roster_players = get_players_from_csv(csv_file)
#
#     if roster_players:
#         print(f"--- Found {len(roster_players)} unique players. Starting Download ---")
#
#         # 3. Loop through and download
#         for player in roster_players:
#             get_player_headshot(player, all_nba_players)
#
#         print("--- Download Complete ---")
#     else:
#         print("--- No players found to download ---")


import pandas as pd
import requests
import shutil
import os
from nba_api.stats.static import players

# --- 1. ID Overrides & Name Corrections ---
# If a name fails to match, or matches the wrong person (old player), hardcode the ID here.
MANUAL_FIXES = {
    # Fixes for duplicates (forcing the active player)
    "Brandon Williams": 1630620,

    # Fixes for string matching failures
    "Jimmy Butler": 202710,
    "Monte Morris": 1628420,
    "Vit Krejci": 1630249,
    "Trey Jemison": 1641998,
    "David Jones García": 1642503,  # David Jones (Exhibit 10/Two-way)
    "Jahmai Mashack": None,  # Likely NCAA (Tennessee) - No NBA ID
    "Egor Dёmin": None,  # Likely NCAA (BYU) - No NBA ID
    "Pacome Dadiet": 1642259,  # Draft Prospect/International - Might not have image yet
    "Ron Holland": 1641842,  # G-League Ignite
    "GG Jackson II": 1631544,
}

# Names to map before searching
NAME_CORRECTIONS = {
    "Alperen Şengün": "Alperen Sengun",
    "Robert Williams": "Robert Williams III",
    "Xavier Tillman Sr.": "Xavier Tillman",
    "Walter Clayton": "Walter Clayton Jr.",
    "Nolan Traoré": "Nolan Traore",
    "Ron Holland": "Ron Holland II",
    "DaRon Holmes": "DaRon Holmes II",
}


def get_players_from_csv(csv_filename):
    try:
        df = pd.read_csv(csv_filename)
        df.columns = [c.strip().replace('▲', '') for c in df.columns]
        if 'Player' not in df.columns:
            return []
        player_list = df['Player'].dropna().unique().tolist()
        return [str(p).strip() for p in player_list if str(p).strip()]
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return []


def get_player_headshot(player_name, all_nba_players, output_folder='player_imgs'):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    filename = f"{output_folder}/{player_name}.png"
    if os.path.exists(filename):
        return  # Skip if exists

    player_id = None

    # STRATEGY 1: Check Manual Fixes
    if player_name in MANUAL_FIXES:
        player_id = MANUAL_FIXES[player_name]
        if player_id is None:
            print(f"⏩ Skipping {player_name} (College/International - No NBA ID)")
            return

    # STRATEGY 2: Search NBA Database
    if not player_id:
        search_name = NAME_CORRECTIONS.get(player_name, player_name)

        # Search by exact name
        found_players = [
            p for p in all_nba_players
            if p['full_name'].lower() == search_name.lower()
        ]

        # Fallback: Remove suffixes (Jr., III)
        if not found_players:
            clean_name = search_name.replace(" Jr.", "").replace(" Sr.", "").replace(" III", "").replace(" II", "")
            found_players = [
                p for p in all_nba_players
                if p['full_name'].lower() == clean_name.lower()
            ]

        if found_players:
            # CRITICAL FIX: Sort by ID descending.
            # Higher ID = Newer Player. This fixes "Brandon Williams" (Old vs New).
            found_players.sort(key=lambda x: x['id'], reverse=True)
            player_id = found_players[0]['id']

    if not player_id:
        print(f"❌ Could not find ID for: {player_name}")
        return

    # Download
    url = f'https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{player_id}.png'
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        r = requests.get(url, stream=True, headers=headers)
        if r.status_code == 200:
            with open(filename, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
            print(f"✅ Saved: {filename}")
        else:
            print(f"⚠️ Image not hosted for {player_name} (ID: {player_id})")
    except Exception as e:
        print(f"❌ Connection error for {player_name}: {e}")


if __name__ == '__main__':
    print("--- Fetching NBA Player Database ---")
    all_nba_players = players.get_players()

    csv_file = "player_stats.csv"
    roster = get_players_from_csv(csv_file)

    if roster:
        print(f"--- Processing {len(roster)} players ---")
        for p in roster:
            get_player_headshot(p, all_nba_players)
        print("--- Done ---")