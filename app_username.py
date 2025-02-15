import pandas as pd
import requests
import time

SHOWDOWN_API_URL = "https://replay.pokemonshowdown.com/"

def fetch_replays_by_username(username):
    """Fetch replays by username using the Pokémon Showdown API."""
    try:
        replays = []
        page = 1
        while True:
            url = f"https://replay.pokemonshowdown.com/search.json?user={username}&page={page}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if not data:
                break  # Stop if there are no more pages

            replays.extend(data)
            print(f"✅ Fetched {len(data)} replays from page {page}")

            if len(data) < 50:
                break  # No more pages to fetch

            page += 1
            time.sleep(1)  # Avoid hitting API limits

        if not replays:
            print(f"❌ No replays found for username: {username}")
            return pd.DataFrame()

        df_replays = pd.DataFrame(replays)
        df_replays["uploadtime"] = pd.to_datetime(df_replays["uploadtime"], unit="s").dt.strftime("%m-%d-%Y")

        return df_replays

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching replays: {e}")
        return pd.DataFrame()

def process_replay_csv(username, csv_file, output_file, team_stats_file):
    """Processes the replay CSV and extracts match data."""
    try:
        df_input = pd.read_csv(csv_file)

        if 'id' not in df_input.columns:
            print("❌ CSV file is missing the 'id' column.")
            return pd.DataFrame(), pd.DataFrame()

        results = []
        for _, row in df_input.iterrows():
            replay_url = f"{SHOWDOWN_API_URL}{row['id']}.json"

            try:
                response = requests.get(replay_url)
                response.raise_for_status()
                replay_data = response.json()

                if "players" not in replay_data or len(replay_data["players"]) < 2:
                    continue

                match_title = f"{replay_data['format']}: {replay_data['players'][0]} vs. {replay_data['players'][1]}"
                match_date = pd.to_datetime(replay_data.get('uploadtime', 0), unit='s').strftime("%m-%d-%Y")
                exact_match = "Yes" if username in replay_data["players"] else "No"

                team = []
                for player in ["p1", "p2"]:
                    if player in replay_data and username in replay_data[player]:
                        team = replay_data.get("log", "").split("|poke|")[1:7]
                        team = [poke.split("|")[1] for poke in team]

                results.append({
                    "Match Title": match_title,
                    "Match Date": match_date,
                    "Replay URL": replay_url,
                    "Exact User Name Match": exact_match,
                    "Team": ", ".join(team) if team else "N/A"
                })

                time.sleep(1)  # Avoid API rate limits

            except requests.exceptions.RequestException as e:
                print(f"❌ Error fetching replay {replay_url}: {e}")

        df_output = pd.DataFrame(results)
        df_output.to_csv(output_file, index=False)
        print(f"✅ Processed replay data saved to {output_file}")

        return df_output, pd.DataFrame()  # Placeholder for team_stats

    except Exception as e:
        print(f"❌ Error processing CSV: {e}")
        return pd.DataFrame(), pd.DataFrame()
