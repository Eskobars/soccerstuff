import os
import json
from date_helper import is_data_up_to_date
from fetchers import fetch_league_standings

def get_standings_data(league_id):
    # Define the directory and file path
    standings_dir = os.path.join('soccerstuff', 'data', 'standings_data')
    filename = os.path.join(standings_dir, f'standings_{league_id}.json')
    
    # Ensure the directory exists
    os.makedirs(standings_dir, exist_ok=True)

    if is_data_up_to_date(filename):
        print(f"Standings data for league {league_id} is up to date, loading from file.")
        with open(filename, 'r') as f:
            standings = json.load(f)
    else:
        print(f"Fetching new standings data for league {league_id}...")
        standings = fetch_league_standings(league_id)
        with open(filename, 'w') as f:
            json.dump(standings, f, indent=4)
        print("Standings data fetched and stored successfully.")
    
    return standings

def extract_team_info(standings_data):
    """
    Extract and return the team rank from the standings data.

    :param standings_data: The JSON response containing league standings.
    :return: A list of dictionaries with team rank and other details.
    """
    # Initialize an empty list to store team ranks
    team_ranks = []

    # Navigate through the nested JSON structure
    try:
        # Extract the list of standings
        standings_list = standings_data.get('response', [])[0].get('league', {}).get('standings', [])[0]

        # Iterate through each team in the standings
        for team in standings_list:
            # Extract relevant details including rank
            team_info = {
                'rank': team.get('rank'),
                'team_name': team.get('team', {}).get('name', 'Unknown'),
                'points': team.get('points'),
                'goalsDiff': team.get('goalsDiff'),
                'form': team.get('form'),
                'status': team.get('status')
            }
            team_ranks.append(team_info)
    
    except (IndexError, KeyError) as e:
        print(f"Error processing standings data: {e}")

    return team_ranks

def get_team_rank(team_ranks, team_name):
    """
    Get the rank of a specific team from the list of team ranks.

    :param team_ranks: List of dictionaries containing team information.
    :param team_name: Name of the team to find the rank for.
    :return: The rank of the team if found, otherwise None.
    """
    for team in team_ranks:
        if team['team_name'] == team_name:
            return team['rank']
    return None
