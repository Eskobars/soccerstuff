import json
import http.client

from datetime import datetime

from config import API_KEY, BASE_URL

def fetch_league_standings(league_id):
    conn = http.client.HTTPSConnection(BASE_URL)
    headers = {
        'x-rapidapi-host': BASE_URL,
        'x-rapidapi-key': API_KEY
    }
    url = f"/standings?league={league_id}&season=2024"  # Adjust endpoint as needed
    conn.request("GET", url, headers=headers)
    res = conn.getresponse()
    data = res.read()
    
    return json.loads(data.decode("utf-8"))

def fetch_match_predictions(fixture_id):
    conn = http.client.HTTPSConnection(BASE_URL)
    headers = {
        'x-rapidapi-host': BASE_URL,
        'x-rapidapi-key': API_KEY
    }
    url = f"/predictions?fixture={fixture_id}"
    conn.request("GET", url, headers=headers)
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode("utf-8"))

def fetch_players_for_fixture(fixture_id):
    conn = http.client.HTTPSConnection(BASE_URL)

    headers = {
        'x-rapidapi-host': BASE_URL,
        'x-rapidapi-key': API_KEY
    }

    url = f"/fixtures/players?fixture={fixture_id}"
    conn.request("GET", url, headers=headers)
    res = conn.getresponse()
    data = res.read()
    
    if res.status != 200:
        print(f"Error fetching players: {res.status} - {res.reason}")
        return None
    
    # Decode the JSON data
    parsed_data = json.loads(data.decode("utf-8"))
    
    return parsed_data

def fetch_injuries_for_fixture(fixture_id):
    conn = http.client.HTTPSConnection(BASE_URL)
    headers = {
        'x-rapidapi-host': BASE_URL,
        'x-rapidapi-key': API_KEY
    }
    url = f"/injuries?fixture={fixture_id}"
    conn.request("GET", url, headers=headers)
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode("utf-8"))


def fetch_team_stats(team_id, league_id):
    conn = http.client.HTTPSConnection(BASE_URL)
    headers = {
        'x-rapidapi-host': BASE_URL,
        'x-rapidapi-key': API_KEY
    }
    url = f"/teams/statistics?season=2024&team={team_id}&league={league_id}"
    conn.request("GET", url, headers=headers)
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode("utf-8"))

def fetch_fixtures_for_day():
    try:
        # Get the current date
        today = datetime.today()
        # Format the date as YYYY-MM-DD
        current_date = today.strftime('%Y-%m-%d')

        conn = http.client.HTTPSConnection(BASE_URL)

        headers = {
            'x-rapidapi-host': BASE_URL,
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