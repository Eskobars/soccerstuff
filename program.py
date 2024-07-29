import json
import os
from datetime import datetime
from config import API_KEY
from fixtures import fetch_fixtures_for_day, filter_fixtures
from injuries import fetch_injuries_for_fixture
from players import fetch_players_for_fixture
from predictions import fetch_match_predictions
from date_helper import is_data_up_to_date

# Define directories for data storage
PREDICTIONS_DIR = 'predictions_data'
INJURIES_DIR = 'injuries_data'
PLAYERS_DIR = 'players_data'

# Create directories if they do not exist
os.makedirs(PREDICTIONS_DIR, exist_ok=True)
os.makedirs(INJURIES_DIR, exist_ok=True)
os.makedirs(PLAYERS_DIR, exist_ok=True)

def rate_fixture(predictions):
    """
    Rate a fixture based on its prediction and return the winning team and comment.
    """
    # Default values
    default_percent_home = 50
    default_percent_draw = 50
    default_percent_away = 50
    default_winner_name = 'Unknown'
    default_comment = "No comment available"

    try:
        # Extract prediction data or use defaults
        percent_home = int(predictions.get('percent', {}).get('home', f'{default_percent_home}%').strip('%'))
        percent_draw = int(predictions.get('percent', {}).get('draw', f'{default_percent_draw}%').strip('%'))
        percent_away = int(predictions.get('percent', {}).get('away', f'{default_percent_away}%').strip('%'))
        winner_name = predictions.get('winner', {}).get('name', default_winner_name)  # Extract winning team name

        # Check both fields for the comment
        comment = predictions.get('winner', {}).get('comment') or predictions.get('winner', {}).get('advice')
        comment = comment if comment is not None else default_comment
    
        # Define rating logic based on percentages
        if percent_home > 70 or percent_away > 70:
            rating = 'three_star'
        elif percent_home > 60 or percent_away > 60:
            rating = 'two_star'
        elif percent_home > 45 and percent_draw > 45:
            rating = 'one_star'
        else:
            rating = 'no_star'

        return rating, winner_name, comment
    except (KeyError, ValueError) as e:
        # Print the structure of predictions for debugging
        print(f"Error processing predictions: {e}")
        print(f"Predictions data: {predictions}")
        return 'no_star', None, "Error retrieving comment"

def get_fixture_prediction(fixture_id):
    """
    Get predictions for a specific fixture. If the data is outdated or unavailable,
    fetch new data and use default values if necessary.
    """
    filename = os.path.join(PREDICTIONS_DIR, f'predictions_data_{fixture_id}.json')

    # Define default prediction values
    default_prediction = {
        'percent': {'home': '70%', 'draw': '20', 'away': '10%'},
        'winner': {'name': 'Unknown', 'comment': 'No comment available', 'advice': 'No advice available'}
    }

    # Check if data is up to date
    if is_data_up_to_date(filename):
        print(f"Predictions data for fixture {fixture_id} is up to date, loading from file.")
        try:
            with open(filename, 'r') as f:
                predictions = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error reading or parsing predictions file: {e}")
            print("Using default prediction values.")
            return default_prediction
    else:
        print(f"Fetching new predictions data for fixture {fixture_id}...")
        try:
            predictions = fetch_match_predictions(fixture_id)
            # Ensure predictions have 'response' and is in list format
            if predictions and 'response' in predictions and isinstance(predictions['response'], list) and len(predictions['response']) > 0:
                with open(filename, 'w') as f:
                    json.dump(predictions, f, indent=4)
                print("Predictions data fetched and stored successfully.")
                return predictions['response'][0]  # Adjust if the structure is different
            else:
                print(f"No predictions available or incorrect format for fixture {fixture_id}. Using default values.")
                return default_prediction
        except Exception as e:
            print(f"Error fetching predictions: {e}")
            print("Using default prediction values.")
            return default_prediction
        
        
def get_injury_data(fixture_id):
    filename = os.path.join(INJURIES_DIR, f'injuries_data_{fixture_id}.json')

    if is_data_up_to_date(filename):
        print(f"Injury data for fixture {fixture_id} is up to date, loading from file.")
        with open(filename, 'r') as f:
            injuries = json.load(f)
    else:
        print(f"Fetching new injury data for fixture {fixture_id}...")
        injuries = fetch_injuries_for_fixture(fixture_id)
        with open(filename, 'w') as f:
            json.dump(injuries, f, indent=4)
        print("Injury data fetched and stored successfully.")
    
    # Extract home and away team injuries
    home_team_injuries = injuries.get('home_team_injuries', [])
    away_team_injuries = injuries.get('away_team_injuries', [])

    return home_team_injuries, away_team_injuries

def get_player_data(fixture_id):
    filename = os.path.join(PLAYERS_DIR, f'players_data_{fixture_id}.json')

    if is_data_up_to_date(filename):
        print(f"Player data for fixture {fixture_id} is up to date, loading from file.")
        with open(filename, 'r') as f:
            players = json.load(f)
    else:
        print(f"Fetching new player data for fixture {fixture_id}...")
        players = fetch_players_for_fixture(fixture_id)
        with open(filename, 'w') as f:
            json.dump(players, f, indent=4)
        print("Player data fetched and stored successfully.")
    
    # Extract home and away team players
    home_team_players = players.get('home_team_players', [])
    away_team_players = players.get('away_team_players', [])

    return home_team_players, away_team_players

def main():
    print("Loading...")
    statuses_to_search = ['NS', 'TBD']
    leagues = ['Ykkönen', 'Kolmonen', 'Kakkonen', 'Liga Profesional Argentina', 'Serie B', 'Serie A']
    one_star_games = []
    two_star_games = []
    three_star_games = []

    fixtures_filename = 'fixtures_data.json'

    if is_data_up_to_date(fixtures_filename):
        print("Fixtures data is up to date, loading from file.")
        with open(fixtures_filename, 'r') as f:
            all_fixtures_data = json.load(f)
    else:
        print("Fetching new fixtures data...")
        all_fixtures_data = fetch_fixtures_for_day()
        with open(fixtures_filename, 'w') as f:
            json.dump(all_fixtures_data, f, indent=4)
        print("Fixtures data fetched and stored successfully")

    # Filter fixtures by status and league
    filtered_fixtures = filter_fixtures(all_fixtures_data, leagues, statuses_to_search)

    for fixture_data in filtered_fixtures:
        fixture_id = fixture_data['fixture']['id']
        league_name = fixture_data['league']['name']
        home_team_name = fixture_data['teams']['home']['name']
        away_team_name = fixture_data['teams']['away']['name']
        
        # Fetch predictions for this fixture
        predictions = get_fixture_prediction(fixture_id)
        if not predictions:
            print(f"No predictions available for fixture {fixture_id} in league {league_name}. Skipping.")
            continue
        
        # Rate the fixture based on predictions
        rating, winning_team, comment = rate_fixture(predictions)
        'three star', 
        # Include the fixture data along with rating, winning team, and comment
        fixture_info = {
            'fixture_data': fixture_data,
            'winning_team': winning_team,
            'comment': comment,
            'league_name': league_name
        }

        if rating == 'three_star':
            three_star_games.append(fixture_info)
        elif rating == 'two_star':
            two_star_games.append(fixture_info)
        elif rating == 'one_star':
            one_star_games.append(fixture_info)

        # Fetch and print injury and player data only for categorized games
        if rating in ['three_star', 'two_star', 'one_star']:
            home_team_injuries, away_team_injuries = get_injury_data(fixture_id)
            home_team_players, away_team_players = get_player_data(fixture_id)

            # Print injury data
            if home_team_injuries:
                print(f"Injuries for {home_team_name}:")
                for injury in home_team_injuries:
                    print(f"  - Player: {injury.get('player')}, Injury: {injury.get('injury')}, Return Date: {injury.get('return_date')}")
            else:
                print(f"No injury information available for {home_team_name}.")

            if away_team_injuries:
                print(f"Injuries for {away_team_name}:")
                for injury in away_team_injuries:
                    print(f"  - Player: {injury.get('player')}, Injury: {injury.get('injury')}, Return Date: {injury.get('return_date')}")
            else:
                print(f"No injury information available for {away_team_name}.")

            # Print player data and compare with injuries
            home_team_warning = ""
            away_team_warning = ""

            if home_team_players:
                print("Home Team Players:")
                for player in home_team_players:
                    print(f"ID: {player['id']}, Name: {player['name']}, Rating: {player['rating']}")
                    # Check if the player is injured
                    if any(injury['player'] == player['name'] for injury in home_team_injuries):
                        print(f"  - Injured: Yes")
                        home_team_warning = "Warning: Key player injured!"
                    else:
                        print(f"  - Injured: No")

            if away_team_players:
                print("Away Team Players:")
                for player in away_team_players:
                    print(f"ID: {player['id']}, Name: {player['name']}, Rating: {player['rating']}")
                    # Check if the player is injured
                    if any(injury['player'] == player['name'] for injury in away_team_injuries):
                        print(f"  - Injured: Yes")
                        away_team_warning = "Warning: Key player injured!"
                    else:
                        print(f"  - Injured: No")

            # Print warnings if any
            if home_team_warning:
                print(f"Home Team Warning: {home_team_warning}")
            if away_team_warning:
                print(f"Away Team Warning: {away_team_warning}")

    # Print categorized games
    print("\nThree Star Games:")
    for game in three_star_games:
        print(f"Fixture: {game['fixture_data']['fixture']['id']}, Winner: {game['winning_team']}, Comment: {game['comment']}")

    print("\nTwo Star Games:")
    for game in two_star_games:
        print(f"Fixture: {game['fixture_data']['fixture']['id']}, Winner: {game['winning_team']}, Comment: {game['comment']}")

    print("\nOne Star Games:")
    for game in one_star_games:
        print(f"Fixture: {game['fixture_data']['fixture']['id']}, Winner: {game['winning_team']}, Comment: {game['comment']}")

if __name__ == "__main__":
    main()
