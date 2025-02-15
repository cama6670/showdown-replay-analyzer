import requests
import json
import pandas as pd
from datetime import datetime

def format_upload_time(timestamp):
    """Convert Unix timestamp to MM-DD-YYYY format."""
    if isinstance(timestamp, int):
        return datetime.utcfromtimestamp(timestamp).strftime('%m-%d-%Y')
    return "Unknown Date"

def fetch_replays_by_username(username):
    """Fetch all replay URLs for a given username using the Pokémon Showdown API."""
    base_url = f"https://replay.pokemonshowdown.com/search.json?user={username}"
    all_replays = []
    page = 1

    while True:
        full_url = f"{base_url}&page={page}"
        print(f"🔍 Fetching: {full_url}")  # Debugging print statement
        
        response = requests.get(full_url)
        if response.status_code != 200:
            print(f"❌ API request failed with status {response.status_code}")
            break
        
        try:
            data = response.json()
            print(f"✅ API Response (Page {page}): {json.dumps(data, indent=2)[:500]}")  # Print first 500 characters for debugging
        except json.JSONDecodeError:
            print("❌ Failed to parse JSON response from Showdown API")
            break

        if not data or "replays" not in data or len(data["replays"]) == 0:
            print(f"✅ No more replays found after page {page}. Stopping search.")
            break

        all_replays.extend(data["replays"])
        print(f"✅ Fetched {len(data['replays'])} replays from page {page}")

        if len(data["replays"]) < 50:
            break  # Stop if less than 50 replays found (end of list)

        page += 1  # Move to next page

    if not all_replays:
        print("❌ No replays found for this username.")
        return pd.DataFrame()

    # Convert to DataFrame
    replay_df = pd.DataFrame(all_replays)
    replay_df['uploadtime'] = replay_df['uploadtime'].apply(format_upload_time)

    print(f"✅ Total replays fetched: {len(replay_df)}")
    return replay_df

def generate_team_id(team, existing_teams):
    """Assign a simple numerical ID for unique teams."""
    if not team:
        return "Unknown_Team"

    sorted_team = ",".join(sorted(team))
    if sorted_team in existing_teams:
        return existing_teams[sorted_team]
    else:
        new_id = len(existing_teams) + 1
        existing_teams[sorted_team] = new_id
        return new_id

def get_showdown_replay_data(username, replay_url, existing_teams):
    """Fetch replay data and extract match details based on username."""
    json_url = replay_url + ".json"

    response = requests.get(json_url)
    if response.status_code != 200:
        print(f"❌ Failed to fetch JSON data for {replay_url}")
        return None

    try:
        replay_data = response.json()
    except json.JSONDecodeError:
        print(f"❌ JSON parsing error for {replay_url}")
        return None

    match_format = replay_data.get('format', 'Unknown Format')
    players = replay_data.get("players", [])
    match_title = f"{match_format}: {' vs. '.join(players)}" if len(players) >= 2 else "Unknown Title"

    upload_time = replay_data.get('uploadtime', None)
    match_date = format_upload_time(upload_time)

    # Determine player slot based on username match
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
    
    if not player_slot:
        player_slot = 'p1'  # Default to Player 1 if username is not found

    team = set()
    for line in replay_data.get('log', '').split('\n'):
        if f"|poke|{player_slot}|" in line:
            pokemon_name = line.split('|')[3].split(',')[0]
            team.add(pokemon_name)

    team_id = generate_team_id(team, existing_teams)

    return {
        'Match Title': match_title,
        'Match Date': match_date,
        'Replay URL': replay_url,
        'Exact User Name Match': "Yes" if exact_user_match else "No",
        'Team': ', '.join(team) if team else "Unknown",
        'Team ID': team_id
    }

def process_replay_csv(username, csv_file, output_file="processed_replays.csv", team_stats_file="team_statistics.csv"):
    """Process fetched replay URLs, extract data, and generate statistics."""
    print(f"📂 Loading CSV: {csv_file}")

    df_input = pd.read_csv(csv_file)

    if "replay_url" not in df_input.columns:
        print("❌ CSV file is missing 'replay_url' column!")
        return pd.DataFrame(), pd.DataFrame()

    replay_urls = df_input["replay_url"].dropna().tolist()
    print(f"🔍 Found {len(replay_urls)} replay URLs for processing.")

    existing_teams = {}
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
