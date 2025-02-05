import requests
import json
from datetime import datetime
import pandas as pd

def format_upload_time(timestamp):
    """Convert Unix timestamp to MM-DD-YYYY format."""
    if isinstance(timestamp, int):
        return datetime.utcfromtimestamp(timestamp).strftime('%m-%d-%Y')
    return "Unknown Date"

def generate_team_id(team, existing_teams):
    """Assign a simple numerical ID for unique teams."""
    if not team:
        return "Unknown_Team"
    
    sorted_team = ",".join(sorted(team))  # Normalize order
    if sorted_team in existing_teams:
        return existing_teams[sorted_team]  # Use existing ID
    else:
        new_id = len(existing_teams) + 1  # Assign next available number
        existing_teams[sorted_team] = new_id
        return new_id

def get_showdown_replay_data(username, replay_url, existing_teams):
    """Fetch replay data and extract match details while ensuring all Bo3 matches are included."""
    if replay_url.endswith('/'):
        replay_url = replay_url[:-1]

    base_id = replay_url.split('/')[-1].split('-')[0]  # Extract base numeric ID

    json_urls = [
        f"https://replay.pokemonshowdown.com/{base_id}.json",  # Short ID format
        f"{replay_url}.json"  # Full ID format (including random string)
    ]

    replay_data = None
    for json_url in json_urls:
        response = requests.get(json_url)
        if response.status_code == 200:
            try:
                replay_data = response.json()
                break  # Stop searching if we find a valid replay
            except json.JSONDecodeError:
                continue  # Try the next format

    if not replay_data:
        return None  # No valid replay found

    match_format = replay_data.get('format', 'Unknown Format')
    players = replay_data.get("players", [])
    match_title = f"{match_format}: {' vs. '.join(players)}" if len(players) >= 2 else "Unknown Title"

    upload_time = replay_data.get('uploadtime', None)
    match_date = format_upload_time(upload_time)  # Convert timestamp to MM-DD-YYYY

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

    # Extract Pokémon team from log
    team = set()
    if player_slot:
        for line in replay_data.get('log', '').split('\n'):
            if f"|poke|{player_slot}|" in line:
                pokemon_name = line.split('|')[3].split(',')[0]
                team.add(pokemon_name)

    team_id = generate_team_id(team, existing_teams)  # Assign simple numerical ID

    # 🛠 **NEW: Handle Bo3 Matches Properly**
    match_number = replay_data.get('id', 'Unknown').split('-')[-1]  # Extract match number
    if match_format.endswith("(Bo3)"):
        match_number = f"Game {match_number[-1]}"  # Tag Game 1, 2, or 3

    return {
        'Match Title': match_title,
        'Match Date': match_date,  # Only keep the formatted date
        'Replay URL': replay_url,
        'Exact User Name Match': "Yes" if exact_user_match else "No",
        'Team': ', '.join(team) if team else "Unknown",
        'Team ID': team_id,  # Add simple numerical Team ID column
        'Match Number': match_number  # Identify Game 1, 2, 3 in Bo3 sets
    }

def process_replay_csv(username, csv_file, output_file="processed_replays.csv", team_stats_file="team_statistics.csv"):
    """Process fetched replay URLs, extract data, and generate statistics."""
    print(f"📂 Loading CSV: {csv_file}")  # Debugging log

    df_input = pd.read_csv(csv_file)

    if "replay_url" not in df_input.columns:
        print("❌ CSV file is missing 'replay_url' column!")
        return pd.DataFrame(), pd.DataFrame()

    replay_urls = df_input["replay_url"].dropna().tolist()
    print(f"🔍 Found {len(replay_urls)} replay URLs for processing.")  # Debug log

    existing_teams = {}  # Dictionary to store team IDs
    results = []
    for url in replay_urls:
        data = get_showdown_replay_data(username, url, existing_teams)
        if data:
            results.append(data)

    if not results:
        print("❌ No valid replay data found!")
        return pd.DataFrame(), pd.DataFrame()

    df_output = pd.DataFrame(results)
    df_output.to_csv(output_file, index=False)
    print(f"✅ Processed replay data saved to {output_file}")

    # Generate team statistics based on unique Team ID
    df_output['Match Date'] = pd.to_datetime(df_output['Match Date'], format="%m-%d-%Y", errors='coerce')
    df_output['Last Used'] = df_output.groupby('Team ID')['Match Date'].transform('max')

    team_stats = df_output.groupby(['Team ID', 'Team', 'Exact User Name Match']).agg(
        Count=('Match Title', 'count'),
        Last_Used=('Last Used', 'max')
    ).reset_index()

    team_stats.to_csv(team_stats_file, index=False)
    print(f"✅ Team stats saved to {team_stats_file}")

    return df_output, team_stats
