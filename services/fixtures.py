import json
import os
from datetime import datetime
from fetchers import fetch_fixtures_for_day
from config import FIXTURES_DIR

def get_fixtures_data():
    filename = os.path.join(FIXTURES_DIR, 'fixtures_data.json')
    metadata_file = os.path.join(FIXTURES_DIR, 'metadata.json')

    # Ensure the directory exists
    os.makedirs(FIXTURES_DIR, exist_ok=True)

    # Fetch the current date in 'YYYY-MM-DD' format
    current_date = datetime.now().strftime('%Y-%m-%d')

    # Function to check if the data is up to date
    def is_data_up_to_date():
        if not os.path.isfile(metadata_file):
            return False
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        stored_date = metadata.get('date')
        return stored_date == current_date

    if is_data_up_to_date():
        with open(filename, 'r') as f:
            all_fixtures_data = json.load(f)
    else:
        all_fixtures_data = fetch_fixtures_for_day()

        with open(filename, 'w') as f:
            json.dump(all_fixtures_data, f, indent=4)
        
        # Update metadata file with the current date
        with open(metadata_file, 'w') as f:
            json.dump({'date': current_date}, f, indent=4)
        
        print("Fixtures data fetched and stored successfully")

    return all_fixtures_data

def filter_fixtures(all_fixtures, leagues, statuses):
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
        if 'league' not in fixture or 'name' not in fixture['league']:
            continue
        
        league_name = fixture['league']['name']
        if league_name not in leagues:
            continue
        
        if 'fixture' not in fixture or 'status' not in fixture['fixture']:
            print(f"Fixture missing status data: {fixture}")
            continue
        
        status_short = fixture['fixture']['status']['short']
        if status_short in statuses:
            filtered_fixtures.append(fixture)

    return filtered_fixtures
