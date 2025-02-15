import requests
import pandas as pd
import ast

SHOWDOWN_API_URL = "https://replay.pokemonshowdown.com/search.json"

def fetch_replays_by_username(username):
    """Fetch replays from Pokémon Showdown based on username."""
    replays = []
    page = 1

    while True:
        response = requests.get(SHOWDOWN_API_URL, params={"user": username, "page": page})
        if response.status_code != 200:
            break  # Stop on request failure
        
        data = response.json()
        if not data:
            break  # Stop if no more replays found
        
        replays.extend(data)
        page += 1  # Move to next page

    # Convert to DataFrame
    replay_df = pd.DataFrame(replays)
    
    # Ensure correct column handling
    if 'id' in replay_df.columns and 'format' in replay_df.columns and 'players' in replay_df.columns:
        replay_df["replay_url"] = "https://replay.pokemonshowdown.com/" + replay_df["id"]
    else:
        return pd.DataFrame()  # Return empty if required columns are missing
    
    return replay_df

def process_replay_csv(username, csv_file, output_file, team_stats_file):
    """Process replay data and save formatted output to CSV."""
    df_input = pd.read_csv(csv_file)

    if 'replay_url' not in df_input.columns:
        return None, None  # If replay_url column is missing, return empty

    replay_urls = df_input['replay_url'].dropna().tolist()
    results = []

    for _, row in df_input.iterrows():
        try:
            # Safely parse players
            players_list = ast.literal_eval(row["players"]) if isinstance(row["players"], str) else []
            match_title = row['format'] + ": " + " vs. ".join(players_list)
        except (SyntaxError, ValueError):
            match_title = row['format'] + ": Unknown vs. Unknown"

        # Append result
        results.append({
            "Match Title": match_title,
            "Match Date": pd.to_datetime(row.get('uploadtime', ''), unit='s').strftime('%m-%d-%Y') if 'uploadtime' in row else '',
            "Replay URL": row["replay_url"]
        })

    df_output = pd.DataFrame(results)
    df_output.to_csv(output_file, index=False)

    return df_output, None  # Team stats handling can be added later if needed
