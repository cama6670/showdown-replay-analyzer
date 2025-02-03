import requests
import json
from datetime import datetime
import pandas as pd

def format_upload_time(timestamp):
    """Convert Unix timestamp to human-readable format."""
    if isinstance(timestamp, int):
        return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    return "Unknown Date"

def get_showdown_replay_data(username, replay_url):
    if replay_url.endswith('/'):
        replay_url = replay_url[:-1]
    json_url = replay_url + ".json"

    response = requests.get(json_url)
    if response.status_code != 200:
        return None

    try:
        replay_data = response.json()
    except json.JSONDecodeError:
        return None

    match_format = replay_data.get('format', 'Unknown Format')
    players = replay_data.get("players", [])
    match_title = f"{match_format}: {' vs. '.join(players)}" if len(players) >= 2 else "Unknown Title"

    upload_time = replay_data.get('uploadtime', None)
    match_date = format_upload_time(upload_time)  # Convert timestamp to readable date

    # Determine player slot and exact match
    exact_user_match = False
    player_slot = None
    if len(players) >= 2:
        p1_name, p2_name = players[0], players[1]
        if username == p1_name:
            player_slot = 'p1'
            exact_user_match = True
        elif username.lower() == p1_name.lower():
            player_slot = 'p1'
        elif username == p2_name:
            player_slot = 'p2'
            exact_user_match = True
        elif username.lower() == p2_name.lower():
            player_slot = 'p2'
    
    # Extract Pokémon team
    team = set()
    if player_slot:
        for line in replay_data.get('log', '').split('\n'):
            if f"|poke|{player_slot}|" in line:
                pokemon_name = line.split('|')[3].split(',')[0]
                team.add(pokemon_name)
    
    return {
        'Match Title': match_title,
        'Match Date': match_date,
        'Team': ', '.join(team),
        'Replay URL': replay_url,
        'Exact User Name Match': "Yes" if exact_user_match else "No"
    }

def process_replay_csv(username, csv_file, output_file="processed_replays.csv", team_stats_file="team_statistics.csv"):
    print(f"📂 Loading CSV: {csv_file}")  # Debugging log

    try:
        df_input = pd.read_csv(csv_file)
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return None, None

    # ✅ FIX: Handle cases where column name might be "replay_url" instead of "url"
    if "url" in df_input.columns:
        replay_urls = df_input["url"].dropna().tolist()
    elif "replay_url" in df_input.columns:
        replay_urls = df_input["replay_url"].dropna().tolist()
    else:
        print("❌ CSV file is missing both 'url' and 'replay_url' columns!")
        return None, None

    print(f"🔍 Found {len(replay_urls)} replay URLs for processing.")  # Debug log

    results = []
    for url in replay_urls:
        data = get_showdown_replay_data(username, url)
        if data:
            results.append(data)

    if not results:
        print("❌ No valid replay data found!")
        return None, None

    df_output = pd.DataFrame(results)
    df_output.to_csv(output_file, index=False)
    print(f"✅ Processed replay data saved to {output_file}")

    # Generate team statistics
    df_output['Match Date'] = pd.to_datetime(df_output['Match Date'], errors='coerce')
    df_output['Last Used'] = df_output.groupby('Team')['Match Date'].transform('max')

    team_stats = df_output.groupby(['Team', 'Exact User Name Match']).agg(
        Count=('Match Title', 'count'),
        Last_Used=('Last Used', 'max')
    ).reset_index()

    team_stats.to_csv(team_stats_file, index=False)
    print(f"✅ Team stats saved to {team_stats_file}")

    return df_output, team_stats
