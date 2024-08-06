import os
import json
from datetime import datetime, timezone, timedelta
from fetchers import fetch_league_standings
from config import STANDINGS_DIR

def is_data_up_to_date(filename, current_date):
    """
    Check if the data in the file is up-to-date based on the current date.

    :param filename: Path to the JSON file.
    :param current_date: The current date to compare against the file's last update.
    :return: True if data is up-to-date, False otherwise.
    """
    try:
        # Check if the file exists and get its last modified date
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(filename)).date()
        
        # Calculate the date range for checking
        date_range_start = current_date - timedelta(days=1)  # Yesterday
        date_range_end = current_date  # Today
        
        # Compare file modification date with the current date
        return date_range_start <= file_mod_time <= date_range_end
    except (OSError, ValueError):
        return False

def get_standings_data(league_id):
    # Define the file path
    filename = os.path.join(STANDINGS_DIR, f'standings_{league_id}.json')
    
    # Ensure the directory exists
    os.makedirs(STANDINGS_DIR, exist_ok=True)
    
    # Use current date for checking
    current_date = datetime.now().date()

    # Check if the data file exists and is up-to-date
    if os.path.exists(filename) and is_data_up_to_date(filename, current_date):
        print(f"Standings data for league {league_id} is up to date, loading from file.")
        with open(filename, 'r') as f:
            standings = json.load(f)
    else:
        print(f"Fetching new standings data for league {league_id}...")
        standings = fetch_league_standings(league_id)
        if standings and 'response' in standings and isinstance(standings['response'], list) and len(standings['response']) > 0:
            with open(filename, 'w') as f:
                json.dump(standings, f, indent=4)
            print("Standings data fetched and stored successfully.")
        else:
            # Handle the case where the response is empty or invalid
            print(f"Empty or invalid standings data received for league {league_id}. Skipping update.")
            # Optionally, set standings to an empty list or handle accordingly
            standings = {'response': []}
    
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
    response_list = standings_data.get('response', [])
    if not response_list:
        print("No response data available.")
        return team_ranks
    
    league_data = response_list[0].get('league', {})
    standings_list = league_data.get('standings', [])
    if not standings_list:
        print("No standings data available.")
        return team_ranks
    
    standings = standings_list[0]  # Assuming standings_list contains one list of standings
    if not isinstance(standings, list):
        print("Standings data is not a list.")
        return team_ranks
    
    # Iterate through each team in the standings
    for team in standings:
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
