import requests
import json
from datetime import datetime
import pandas as pd

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
    match_date = datetime.utcfromtimestamp(upload_time).strftime('%Y-%m-%d') if isinstance(upload_time, int) else "Unknown Date"
    
    # Determine player slot and exact match
    exact_user_match = False
    player_slot = None
    if len(players) >= 2:
        p1_name, p2_name = players[0], players[1]
        if username == p1_name:
            player_slot = 'p1'
            exact_user_match = username == p1_name  # Case-sensitive match
        elif username.lower() == p1_name.lower():
            player_slot = 'p1'
        elif username == p2_name:
            player_slot = 'p2'
            exact_user_match = username == p2_name  # Case-sensitive match
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
    df_input = pd.read_csv(csv_file)
    if 'url' not in df_input.columns:
        return None
    
    replay_urls = df_input['url'].dropna().tolist()
    results = []
    for url in replay_urls:
        data = get_showdown_replay_data(username, url)
        if data:
            results.append(data)

    df_output = pd.DataFrame(results)
    df_output.to_csv(output_file, index=False)
    
    # Generate team statistics
    df_output['Match Date'] = pd.to_datetime(df_output['Match Date'], errors='coerce')
    df_output['Last Used'] = df_output.groupby('Team')['Match Date'].transform('max')

    team_stats = df_output.groupby(['Team', 'Exact User Name Match']).agg(
        Count=('Match Title', 'count'),
        Last_Used=('Last Used', 'max')
    ).reset_index()

    team_stats.to_csv(team_stats_file, index=False)
    return df_output, team_stats
