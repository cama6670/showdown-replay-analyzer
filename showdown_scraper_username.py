import requests
import pandas as pd
import json
import time
import ast 

SHOWDOWN_API_URL = "https://replay.pokemonshowdown.com/search.json"

def fetch_replays_by_username(username):
    """Fetch replays for a given username using Showdown's API"""
    all_replays = []
    page = 1

    print(f"🔍 Searching for replays of '{username}'...")

    while True:
        params = {"user": username, "page": page}
        print(f"🌐 Fetching page {page} from {SHOWDOWN_API_URL} with params: {params}")

        response = requests.get(SHOWDOWN_API_URL, params=params)
        if response.status_code != 200:
            print(f"❌ Error fetching page {page}: {response.status_code}")
            break

        replays = response.json()
        if not replays:
            print("✅ Pagination Complete: No more replays found.")
            break

        for replay in replays:
            replay_id = replay["id"]
            teams, opponent = fetch_team_from_replay(replay_id, username)
            replay["teams"] = teams  # Store extracted full team data
            replay["opponent"] = opponent  # Store opponent's actual name

        all_replays.extend(replays)
        print(f"✅ Fetched {len(replays)} replays from page {page}")

        page += 1
        time.sleep(1)  # Avoid excessive requests

    if not all_replays:
        return pd.DataFrame()

    df = pd.DataFrame(all_replays)
    df.to_csv("fetched_replays.csv", index=False)
    print(f"✅ Saved {len(df)} replays to fetched_replays.csv")
    return df


def fetch_team_from_replay(replay_id, username):
    """Fetches a replay and extracts full teams + opponent's name"""
    replay_url = f"https://replay.pokemonshowdown.com/{replay_id}.json"
    response = requests.get(replay_url)

    if response.status_code != 200:
        print(f"❌ Error fetching replay {replay_id}")
        return "{}", "Unknown"

    data = response.json()
    replay_log = data.get("log", "")

    print(f"🔍 Debug: Raw Replay Log for {replay_id}")
    print(replay_log[:500])  # Print first 500 characters to check log structure

    teams, opponent = extract_teams_and_opponent(replay_log, username)

    return json.dumps(teams), opponent  # Store teams as JSON string and return opponent name


def extract_teams_and_opponent(replay_log, username):
    """Extracts full teams and finds opponent's name from the replay log safely."""
    teams = {"p1": [], "p2": []}
    opponent = "Unknown"
    lines = replay_log.split("\n")

    player_dict = {}  # Store player mapping (p1 -> player1, p2 -> player2)
    for line in lines:
        parts = line.split("|")
        if len(parts) < 4:  # Ensure there are at least 4 parts
            continue  # Skip this line if it's too short

        if parts[1] == "player":
            player_slot, player_name = parts[2], parts[3]
            player_dict[player_slot] = player_name

        if parts[1] == "poke" and len(parts) >= 4:  # Check that parts[3] exists
            player, pokemon = parts[2], parts[3].split(",")[0]
            if player in teams:
                teams[player].append(pokemon)

    # Determine opponent based on who isn't the searched username
    for slot, player_name in player_dict.items():
        if player_name.lower() != username.lower():
            opponent = player_name
            break

    return teams, opponent



def assign_sequential_team_ids(team_list):
    """Assigns a unique numeric ID to each unique set of six Pokémon."""
    team_id_map = {}
    current_id = 1  # Start numbering from 1

    def get_team_id(team):
        """Returns existing ID if team is found, otherwise assigns a new one."""
        nonlocal current_id
        sorted_team = tuple(sorted(team))  # Ensure consistent order
        if sorted_team not in team_id_map:
            team_id_map[sorted_team] = current_id
            current_id += 1
        return team_id_map[sorted_team]

    return get_team_id


def process_replay_csv(username, input_csv, output_csv, team_stats_csv):
    """Processes replay data and generates team statistics"""
    df_input = pd.read_csv(input_csv)

    if df_input.empty:
        print("❌ No data to process.")
        return pd.DataFrame(), pd.DataFrame()

    # Ensure 'teams' and 'opponent' columns exist
    if "teams" not in df_input.columns:
        print("⚠ Warning: 'teams' column missing in CSV. Ensure teams are fetched before processing.")
        df_input["teams"] = "{}"  # Default empty JSON

    if "opponent" not in df_input.columns:
        df_input["opponent"] = "Unknown"

    # Convert stored JSON strings into dictionaries
    df_input["teams"] = df_input["teams"].apply(lambda x: json.loads(x) if isinstance(x, str) else x)

    # ✅ **Fix: Ensure 'players' is properly parsed**
    if "players" in df_input.columns:
        df_input["players"] = df_input["players"].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith("[") else x
        )

        # Ensure player names are properly extracted
        df_input["Match Title"] = df_input.apply(
            lambda row: f"{row['format']}: {row['players'][0]} vs. {row['players'][1]}"
            if isinstance(row["players"], list) and len(row["players"]) == 2 
            else f"{row['format']}: ??? vs. ???",
            axis=1
        )
    else:
        df_input["Match Title"] = df_input['format'] + ": ??? vs. ???"  # Fallback

    # ✅ **Fix: Debug missing titles**
    df_missing_titles = df_input[df_input["Match Title"].str.contains("\?\?\?")]
    if not df_missing_titles.empty:
        print(f"⚠ Warning: Some replays are missing Match Titles! Here are a few:")
        print(df_missing_titles[["format", "players"]].head(5))

    # Convert timestamp to readable format
    df_input['Match Date'] = pd.to_datetime(df_input['uploadtime'], unit='s').dt.strftime("%m-%d-%Y")

    # ✅ **Ensure we assign unique Team IDs**
    get_team_id = assign_sequential_team_ids(df_input["teams"].apply(lambda x: x.get("p1", [])))
    df_input["Team"] = df_input["teams"].apply(lambda x: ", ".join(x.get("p1", [])))  # Store team as string
    df_input["Team ID"] = df_input["teams"].apply(lambda x: get_team_id(x.get("p1", [])))

    # ✅ **Processed Replay Data Table**
    df_output = df_input[['Team ID', 'Match Title', 'Match Date', 'Replay URL', 'Team']]
    df_output.to_csv(output_csv, index=False)

    # ✅ **Team Statistics Table**
    team_stats_df = df_input.groupby(["Team ID", "Team"]).agg(
        Times_Used=("Team ID", "count"),
        Last_Used=("Match Date", "max")  # Get most recent date team was used
    ).reset_index()

    team_stats_df.to_csv(team_stats_csv, index=False)

    return df_output, team_stats_df
    team_stats_df.to_csv(team_stats_csv, index=False)

    return df_output, team_stats_df
