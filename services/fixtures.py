import json
import os

from datetime import datetime
from fetchers import fetch_fixtures_for_day, fetch_fixture
from helpers.data.latest_file import find_latest_rated_fixtures, find_latest_file
from helpers.data.fetch_data import fetch_data_with_rate_limit

from config import FIXTURES_DIR, RATINGS_DIR, BETS_DIR

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

def get_fixture(fixture_id):
    """
    Fetch the fixture score for a specific fixture ID.
    Fetches from local storage or an external API if data is missing or outdated.
    """
    filename = os.path.join(FIXTURES_DIR, f'fixture_{fixture_id}_score.json')
    metadata_file = os.path.join(FIXTURES_DIR, f'metadata_{fixture_id}.json')
    
    os.makedirs(FIXTURES_DIR, exist_ok=True)
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    def is_data_valid():
        if not os.path.isfile(filename) or not os.path.isfile(metadata_file):
            return False
        
        # Check if the score file is empty
        if os.path.getsize(filename) == 0:
            return False
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        stored_date = metadata.get('date')
        return stored_date == current_date
    
    if is_data_valid():
        with open(filename, 'r') as f:
            fixture_score_data = json.load(f)
    else:
        fixture_score_data = fetch_data_with_rate_limit(fetch_fixture, fixture_id)
        
        with open(filename, 'w') as f:
            json.dump(fixture_score_data, f, indent=4)
        
        # Update metadata file with the current date
        with open(metadata_file, 'w') as f:
            json.dump({'date': current_date}, f, indent=4)
        
        print(f"Fixture score data for fixture {fixture_id} fetched and stored successfully")
    
    return fixture_score_data

def filter_fixtures(all_fixtures, statuses, countries):
    """
    Filters fixtures based on provided statuses and countries.

    :param all_fixtures: List of all fixture data.
    :param statuses: List of statuses to include (e.g., ['NS', 'TBD']).
    :param countries: List of countries to include (e.g., ['Argentina', 'England']).
    :return: List of filtered fixtures.
    """
    filtered_fixtures = []

    if isinstance(all_fixtures, dict):
        if 'response' in all_fixtures:
            all_fixtures = all_fixtures['response']
        else:
            print("No 'response' key found in fixtures data.")
            return filtered_fixtures
    elif not isinstance(all_fixtures, list):
        print("Invalid fixtures data provided.")
        return filtered_fixtures

    for fixture in all_fixtures:
        if 'league' not in fixture or 'fixture' not in fixture:
            print(f"Fixture missing league or fixture data: {fixture}")
            continue
        
        league_country = fixture['league'].get('country', '')

        if league_country not in countries:
            continue
        
        if 'status' not in fixture['fixture']:
            print(f"Fixture missing status data: {fixture}")
            continue
        
        status_short = fixture['fixture']['status']['short']
        if status_short in statuses:
            filtered_fixtures.append(fixture)

    return filtered_fixtures

def remove_duplicates(game_list):
    seen = set()
    unique_games = []
    for game in game_list:
        game_str = json.dumps(game, sort_keys=True)
        if game_str not in seen:
            seen.add(game_str)
            unique_games.append(game)
    return unique_games

def load_rated_fixtures():
    latest_file = find_latest_rated_fixtures(RATINGS_DIR)
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
            'one_star_games': remove_duplicates(data.get('one_star_games', [])),
            'two_star_games': remove_duplicates(data.get('two_star_games', [])),
            'three_star_games': remove_duplicates(data.get('three_star_games', [])),
            'no_star_games': remove_duplicates(data.get('no_star_games', []))
        }

def save_rated_fixtures(one_star_games, two_star_games, three_star_games, no_star_games):
    date_str = datetime.now().strftime('%Y-%m-%d')
    file_path = os.path.join(RATINGS_DIR, f'rated_fixtures_{date_str}.json')
    
    rated_fixtures = load_rated_fixtures()

    rated_fixtures['one_star_games'] = remove_duplicates(rated_fixtures.get('one_star_games', []) + one_star_games)
    rated_fixtures['two_star_games'] = remove_duplicates(rated_fixtures.get('two_star_games', []) + two_star_games)
    rated_fixtures['three_star_games'] = remove_duplicates(rated_fixtures.get('three_star_games', []) + three_star_games)
    rated_fixtures['no_star_games'] = remove_duplicates(rated_fixtures.get('no_star_games', []) + no_star_games)

    rated_fixtures['one_star_games'].sort(key=lambda x: str(x))
    rated_fixtures['two_star_games'].sort(key=lambda x: str(x))
    rated_fixtures['three_star_games'].sort(key=lambda x: str(x))
    rated_fixtures['no_star_games'].sort(key=lambda x: str(x))

    with open(file_path, 'w') as file:
        json.dump(rated_fixtures, file, indent=4)

def get_fixture_score(fixture_id):
    fixture_data = get_fixture(fixture_id)
    
    actual_home_score = fixture_data['score']['fulltime']['home']
    actual_away_score = fixture_data['score']['fulltime']['away']
    
    if actual_home_score is None or actual_away_score is None:
        print(f"Score data not available for fixture {fixture_id}")
        return None, None  

    return actual_home_score, actual_away_score

