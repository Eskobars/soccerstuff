import json
import os

from datetime import datetime
from fetchers import fetch_fixtures_for_day
from helpers.data.latest_file import find_latest_file
from helpers.data.fetch_data import fetch_data_with_rate_limit

from config import FIXTURES_DIR, RATINGS_DIR

def get_fixtures_data():
    filename = os.path.join(FIXTURES_DIR, 'fixtures_data.json')
    metadata_file = os.path.join(FIXTURES_DIR, 'metadata.json')
    
    # Ensure the directory exists
    os.makedirs(FIXTURES_DIR, exist_ok=True)
    
    # Fetch the current date in 'YYYY-MM-DD' format
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Function to check if the data is up to date and not empty
    def is_data_valid():
        if not os.path.isfile(filename) or not os.path.isfile(metadata_file):
            return False
        
        # Check if fixtures_data.json is empty
        if os.path.getsize(filename) == 0:
            return False
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        stored_date = metadata.get('date')
        return stored_date == current_date
    
    if is_data_valid():
        with open(filename, 'r') as f:
            all_fixtures_data = json.load(f)
    else:
        all_fixtures_data = fetch_data_with_rate_limit(fetch_fixtures_for_day)
        
        # Save the new fixtures data
        with open(filename, 'w') as f:
            json.dump(all_fixtures_data, f, indent=4)
        
        # Update metadata file with the current date
        with open(metadata_file, 'w') as f:
            json.dump({'date': current_date}, f, indent=4)
        
        print("Fixtures data fetched and stored successfully")
    
    return all_fixtures_data

def filter_fixtures(all_fixtures, statuses, countries):
    """
    Filters fixtures based on provided statuses and countries.

    :param all_fixtures: List of all fixture data.
    :param statuses: List of statuses to include (e.g., ['NS', 'TBD']).
    :param countries: List of countries to include (e.g., ['Argentina', 'England']).
    :return: List of filtered fixtures.
    """
    filtered_fixtures = []

    # Check if data is a dictionary
    if isinstance(all_fixtures, dict):
        # Extract fixtures from the 'response' key if it exists
        if 'response' in all_fixtures:
            all_fixtures = all_fixtures['response']
        else:
            print("No 'response' key found in fixtures data.")
            return filtered_fixtures
    elif not isinstance(all_fixtures, list):
        print("Invalid fixtures data provided.")
        return filtered_fixtures

    for fixture in all_fixtures:
        # Ensure 'league' and 'fixture' keys exist
        if 'league' not in fixture or 'fixture' not in fixture:
            print(f"Fixture missing league or fixture data: {fixture}")
            continue
        
        league_country = fixture['league'].get('country', '')

        # Check if the country matches the filtering criteria
        if league_country not in countries:
            continue
        
        # Ensure 'status' key exists in fixture data
        if 'status' not in fixture['fixture']:
            print(f"Fixture missing status data: {fixture}")
            continue
        
        status_short = fixture['fixture']['status']['short']
        if status_short in statuses:
            filtered_fixtures.append(fixture)

    return filtered_fixtures

def load_rated_fixtures():
    latest_file = find_latest_file(RATINGS_DIR)
    if latest_file is None:
        return {
            'one_star_games': [],
            'two_star_games': [],
            'three_star_games': [],
            'no_star_games': []
        }

    file_path = os.path.join(RATINGS_DIR, latest_file)
    with open(file_path, 'r') as file:
        data = json.load(file)
        return {
            'one_star_games': data.get('one_star_games', []),
            'two_star_games': data.get('two_star_games', []),
            'three_star_games': data.get('three_star_games', []),
            'no_star_games': data.get('no_star_games', [])
        }

def save_rated_fixtures(one_star_games, two_star_games, three_star_games, no_star_games):
    date_str = datetime.now().strftime('%Y-%m-%d')
    file_path = os.path.join(RATINGS_DIR, f'rated_fixtures_{date_str}.json')
    
    rated_fixtures = load_rated_fixtures()
    
    rated_fixtures.setdefault('one_star_games', []).extend(one_star_games)
    rated_fixtures.setdefault('two_star_games', []).extend(two_star_games)
    rated_fixtures.setdefault('three_star_games', []).extend(three_star_games)
    rated_fixtures.setdefault('no_star_games', []).extend(no_star_games)
    
    with open(file_path, 'w') as file:
        json.dump(rated_fixtures, file, indent=4)