import requests
import pandas as pd
import time

SHOWDOWN_API_URL = "https://replay.pokemonshowdown.com/search.json"

def fetch_replays_by_username(username):
    """
    Fetches all available replays for a given username from the Pokémon Showdown API.
    Uses pagination to get more than 50 replays.
    """
    print(f"🔄 Fetching replays for {username}...")  # Debugging message
    all_replays = []
    page = 1  # Start from page 1
    
    while True:
        print(f"🔍 Fetching page {page}...")
        params = {"user": username, "page": page}
        response = requests.get(SHOWDOWN_API_URL, params=params)

        if response.status_code != 200:
            print(f"❌ Error fetching replays: {response.status_code}")
            break

        replays = response.json()

        if not replays:
            print(f"✅ Pagination complete. Total replays fetched: {len(all_replays)}")
            break  # Stop fetching if no more replays are returned

        all_replays.extend(replays)
        page += 1
        time.sleep(1)  # Respect API rate limits

    if not all_replays:
        return pd.DataFrame()  # Return an empty DataFrame if no data found

    df = pd.DataFrame(all_replays)
    print(f"✅ Successfully fetched {len(df)} replays for {username}.")
    return df

def process_replay_csv(username, csv_file, output_file, team_stats_file):
    """
    Processes replay data from the fetched CSV, extracts team compositions, match titles,
    and formats the data for analysis.
    """
    print(f"📂 Loading CSV: {csv_file}")
    df_input = pd.read_csv(csv_file)

    if 'id' not in df_input.columns or 'players' not in df_input.columns:
        print("❌ CSV file is missing required columns!")
        return pd.DataFrame(), pd.DataFrame()  # Return empty DataFrames

    results = []

    for _, row in df_input.iterrows():
        match_id = row['id']
        match_url = f"https://replay.pokemonshowdown.com/{match_id}"
        match_title = row['format'] + ": " + " vs. ".join(eval(row['players']))
        match_date = pd.to_datetime(row['uploadtime'], unit='s').strftime('%m-%d-%Y')

        # Determine if the user was in this match
        players = eval(row['players'])  # Convert from string to list
        exact_match = "Yes" if username in players else "No"

        results.append({
            "Match Title": match_title,
            "Match Date": match_date,
            "Replay URL": match_url,
            "Exact User Name Match": exact_match
        })

    df_output = pd.DataFrame(results)
    df_output.to_csv(output_file, index=False)
    print(f"✅ Processed replay data saved to {output_file}")

    # Compute team statistics
    df_output['Team'] = df_output.groupby('Replay URL')['Match Title'].transform(lambda x: ', '.join(x))
    df_output['Last Used'] = df_output.groupby('Team')['Match Date'].transform('max')

    team_stats = df_output.groupby('Team').agg(
        Total_Count=('Match Title', 'count'),
        Last_Used=('Last Used', 'max')
    ).reset_index()

    team_stats.to_csv(team_stats_file, index=False)
    print(f"✅ Team statistics saved to {team_stats_file}")

    return df_output, team_stats
