import http.client
from datetime import datetime
import json
from config import API_KEY  # Import the API key

def fetch_fixtures_for_day():
    try:
        # Get the current date
        today = datetime.today()
        # Format the date as YYYY-MM-DD
        current_date = today.strftime('%Y-%m-%d')

        conn = http.client.HTTPSConnection("v3.football.api-sports.io")

        headers = {
            'x-rapidapi-host': "v3.football.api-sports.io",
            'x-rapidapi-key': API_KEY
        }

        # Create the request URL for fixtures of the current day
        url = f"/fixtures?date={current_date}"
        conn.request("GET", url, headers=headers)

        res = conn.getresponse()
        data = res.read()

        # Check the response status
        if res.status != 200:
            print(f"Error fetching fixtures: {res.status} - {res.reason}")
            return None

        # Decode the JSON data
        parsed_data = json.loads(data.decode("utf-8"))

        # Check for the expected structure in the data
        if 'response' not in parsed_data:
            print("No 'response' field found in the data.")
            return None

        return parsed_data

    except Exception as e:
        print(f"An error occurred while fetching fixtures: {e}")
        return None
    
def extract_core_team_name(name_fragment):
    """
    Extract the core team name from a name fragment. For simplicity,
    this example assumes that the core name can be derived by splitting
    the name fragment on common delimiters and taking the first part.
    """
    # Define common delimiters
    delimiters = [' ', '-', ':', '/', 'vs']
    
    # Split by delimiters and return the first part
    for delimiter in delimiters:
        if delimiter in name_fragment:
            return name_fragment.split(delimiter)[0].strip()
    
    # If no delimiter is found, return the name fragment itself
    return name_fragment.strip()

def get_fixture_id(all_fixtures, team_name_fragment):
    if not all_fixtures or 'response' not in all_fixtures:
        print("Invalid fixtures data provided.")
        return None

    try:
        # Normalize the team name fragment and extract the core name
        team_name_fragment_core = extract_core_team_name(team_name_fragment).lower()

        for fixture in all_fixtures['response']:
            # Access team names and fixture id directly from the JSON structure
            home_team_name = fixture['teams']['home']['name'].lower().strip()
            away_team_name = fixture['teams']['away']['name'].lower().strip()
            fixture_id = fixture['fixture']['id']

            # Check if the core team name is a substring of either team name
            if team_name_fragment_core in home_team_name or team_name_fragment_core in away_team_name:
                return fixture_id

    except KeyError as e:
        print(f"Key error: {e}")
        return None

    # If no matching fixture is found, return None
    return None

def filter_fixtures(all_fixtures, leagues, statuses):
    """
    Filter fixtures based on league name and status.
    """
    filtered_fixtures = []

    # Debugging print statements
    print(f"All fixtures data type: {type(all_fixtures)}")
    
    # Check if data is a dictionary
    if isinstance(all_fixtures, dict):
        # Print keys to understand structure
        print(f"Keys in all fixtures data: {list(all_fixtures.keys())}")

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
        # Check league data
        if 'league' not in fixture or 'name' not in fixture['league']:
            print(f"Fixture missing league data: {fixture}")
            continue
        
        league_name = fixture['league']['name']
        if league_name not in leagues:
            continue
        
        # Check status data
        if 'fixture' not in fixture or 'status' not in fixture['fixture']:
            print(f"Fixture missing status data: {fixture}")
            continue
        
        status_short = fixture['fixture']['status']['short']
        if status_short in statuses:
            filtered_fixtures.append(fixture)

    return filtered_fixtures
