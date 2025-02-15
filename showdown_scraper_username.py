import pandas as pd
import requests
import time

SHOWDOWN_API_URL = "https://replay.pokemonshowdown.com/"

def fetch_replays_by_username(username):
    """
    Fetches all replay data for a given username using pagination.
    """
    fetched_replays = []
    page = 1
    while True:
        url = f"https://pokemonshowdown.com/api/replays/{username}?page={page}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error fetching page {page}: {response.status_code}")
            break

        data = response.json()
        if not data.get("replays"):
            break  # No more replays found

        fetched_replays.extend(data["replays"])
        page += 1
        time.sleep(1)  # Avoid spamming the API

    return pd.DataFrame(fetched_replays)

def process_replay_csv(username, csv_file, output_file, team_stats_file):
    """
    Processes replay data from the fetched results and optional uploaded CSV.
    """
    df_input = pd.read_csv(csv_file)
    
    if 'Replay URL' not in df_input.columns:
        raise ValueError("CSV must contain a 'Replay URL' column.")
    
    replay_urls = df_input['Replay URL'].dropna().tolist()
    results = []

    for url in replay_urls:
        replay_id = url.split("/")[-1]
        response = requests.get(f"{SHOWDOWN_API_URL}{replay_id}.json")
        
        if response.status_code == 200:
            data = response.json()
            match_title = f"{data['format']}: {username} vs. Opponent"
            match_date = pd.to_datetime(data.get('uploadtime', 0), unit='s').strftime('%m-%d-%Y')
            team = ", ".join(data.get("p1team", []))  # Adjust based on actual team data structure
            results.append({
                "Match Title": match_title,
                "Match Date": match_date,
                "Replay URL": url,
                "Team": team
            })
        time.sleep(0.5)  # Avoid excessive requests

    df_output = pd.DataFrame(results)
    df_output.to_csv(output_file, index=False)
    print(f"Processed replay data saved to {output_file}")

    # Generate team usage statistics
    team_stats = df_output.groupby("Team").size().reset_index(name="Usage Count")
    team_stats.to_csv(team_stats_file, index=False)
    print(f"Team statistics saved to {team_stats_file}")

    return df_output, team_stats
