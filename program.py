import os
import time
import json
import functools
from datetime import datetime
from services.fixtures import filter_fixtures, get_fixtures_data
from services.standings import get_standings_data, extract_team_info, get_team_rank
from services.injuries import get_injury_data
from services.predictions import rate_fixture, get_fixture_prediction, determine_rating
from services.players import get_player_data, get_key_players_by_team
from config import PREDICTIONS_DIR, INJURIES_DIR, PLAYERS_DIR, STANDINGS_DIR, RATINGS_DIR

# Create directories if they do not exist
os.makedirs(PREDICTIONS_DIR, exist_ok=True)
os.makedirs(INJURIES_DIR, exist_ok=True)
os.makedirs(PLAYERS_DIR, exist_ok=True)
os.makedirs(STANDINGS_DIR, exist_ok=True)
os.makedirs(RATINGS_DIR, exist_ok=True)

def find_latest_file(directory):
    files = [f for f in os.listdir(directory) if f.startswith('rated_fixtures_') and f.endswith('.json')]
    if not files:
        return None

    def extract_date(filename):
        # Extract date part between 'rated_fixtures_' and '.json'
        try:
            # Extract the date part
            date_str = filename[len('rated_fixtures_'): -len('.json')]
            # Parse the date
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            print(f"Date extraction failed for filename: {filename}")
            return None

    # Create a list of (filename, date) tuples
    files_with_dates = [(f, extract_date(f)) for f in files]
    # Filter out files with invalid dates
    valid_files_with_dates = [(f, d) for f, d in files_with_dates if d is not None]

    if not valid_files_with_dates:
        return None

    # Find the file with the latest date
    latest_file = max(valid_files_with_dates, key=lambda x: x[1])[0]
    return latest_file

# Helper function to determine if data is valid (not None and not empty)
def is_valid_data(data):
    return data is not None and len(data) > 0

# Function to find team data by team name
def find_team_data_by_name(team_name, team_info):
    for team in team_info:
        if team['team_name'] == team_name:
            return team
    return None

# Generic function to handle rate limiting and null values
def fetch_data_with_rate_limit(fetch_function, *args, max_requests_per_minute=10):
    request_count = 0
    start_time = time.time()
    time.sleep(3)

    @functools.wraps(fetch_function)
    def wrapper():
        while True:
            nonlocal request_count, start_time
            current_time = time.time()

            # Check if the minute has passed and reset request count if necessary
            if current_time - start_time >= 60:
                request_count = 0
                start_time = current_time

            # Rate limit check
            if request_count >= max_requests_per_minute:
                print("Request limit reached. Waiting for 61 seconds...")
                time.sleep(61)  # Wait for 61 seconds before retrying
                request_count = 0  # Reset request count after waiting

            # Attempt to fetch data
            try:
                data = fetch_function(*args)
                request_count += 1
                # Check for rate limit error in the response
                if 'errors' in data and 'rateLimit' in data['errors']:
                    print("Rate limit error detected. Waiting for 60 seconds...")
                    time.sleep(61)  # Wait for 61 seconds if rate limit error is detected
                    continue  # Retry fetching data
                
                return data  # Return data if no error is detected
            except Exception as e:
                print(f"Error fetching data: {e}")
                print("Retrying in 61 seconds...")
                time.sleep(61)  # Wait before retrying in case of error

    return wrapper()

def load_standings_data(league_id):
    """Load standings data from a file and ensure it contains valid content."""
    file_path = os.path.join(STANDINGS_DIR, f'standings_{league_id}.json')
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                # Check if data is not empty and contains the expected 'response' field
                if data and 'response' in data and isinstance(data['response'], list) and len(data['response']) > 0:
                    return data
        except (FileNotFoundError, KeyError, IndexError, ValueError, json.JSONDecodeError) as e:
            print(f"Error reading standings data from {file_path}: {e}")
    
    return None

def save_standings_data(league_id, data):
    """Save standings data to a file."""
    file_path = os.path.join(STANDINGS_DIR, f'standings_{league_id}.json')
    with open(file_path, 'w') as file:
        json.dump(data, file)

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
        json.dump(rated_fixtures, file, indent=4)  # Added indent for readability


def save_rated_fixtures(one_star_games, two_star_games, three_star_games, no_star_games):
    # Generate the file name with the current date
    date_str = datetime.now().strftime('%Y-%m-%d')
    file_path = os.path.join(RATINGS_DIR, f'rated_fixtures_{date_str}.json')
    
    # Load existing fixtures
    rated_fixtures = load_rated_fixtures()
    
    # Use the get method with a default value to prevent KeyError
    rated_fixtures.setdefault('one_star_games', []).extend(one_star_games)
    rated_fixtures.setdefault('two_star_games', []).extend(two_star_games)
    rated_fixtures.setdefault('three_star_games', []).extend(three_star_games)
    rated_fixtures.setdefault('no_star_games', []).extend(no_star_games)
    
    with open(file_path, 'w') as file:
        json.dump(rated_fixtures, file, indent=4)  # Added indent for readability

def main():
    print("Loading...")

    statuses_to_search = ['NS', 'TBD']
    trusted_leagues = {
        'Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1',
        'Primeira Liga', 'Eredivisie', 'Major League Soccer',
        'Brasileirão Serie A', 'Argentine Primera División'
    }
    trusted_countries = {
        'England', 'Spain', 'Italy', 'Germany', 'France', 'Portugal',
        'Netherlands', 'USA', 'Brazil', 'Argentina'
    }

    rated_fixtures = load_rated_fixtures()
    processed_fixture_ids = {
        fixture['fixture_data']['fixture']['id']
        for rating in rated_fixtures.values()
        for fixture in rating
    }

    one_star_games = []
    two_star_games = []
    three_star_games = []
    no_star_games = []
    league_standings_cache = {}
    failed_league_ids = set()  # Set to track league IDs that failed

    all_fixtures_data = fetch_data_with_rate_limit(get_fixtures_data)

    filtered_fixtures = filter_fixtures(all_fixtures_data, statuses_to_search, trusted_countries)

    for fixture_data in filtered_fixtures:

        fixture_id = fixture_data['fixture']['id']
        if fixture_id in processed_fixture_ids:
            continue
        
        fixture_id = fixture_data['fixture']['id']
        league_name = fixture_data['league']['name']
        league_id = fixture_data['league']['id']
        home_team_name = fixture_data['teams']['home']['name']
        away_team_name = fixture_data['teams']['away']['name']
        away_team_points = 0
        home_team_points = 0
        warning = ""
        winner_name = ""
        points_winner_name = ""

        # Skip fetching standings data if league_id is in the failed set
        if league_id in failed_league_ids:
            print(f"League ID {league_id} has previously failed. Skipping fixture {fixture_id}.")
            fixture_info = {
                'fixture_data': fixture_data,
                'winning_team': None,
                'comment': "Previously failed league",
                'league_name': league_name,
                'warning': warning
            }
            no_star_games.append(fixture_info)
            continue

        # Check if standings data is already cached or in files
        if league_id not in league_standings_cache:
            standings_data = load_standings_data(league_id)
            if not standings_data:
                standings_data = fetch_data_with_rate_limit(get_standings_data, league_id)
                if not standings_data or not standings_data.get('response'):
                    print(f"Standings data is empty or invalid for league {league_id}. Skipping fixture {fixture_id}.")
                    # Add to failed set and continue
                    failed_league_ids.add(league_id)
                    fixture_info = {
                        'fixture_data': fixture_data,
                        'winning_team': None,
                        'comment': "No standings data available",
                        'league_name': league_name,
                        'warning': warning
                    }
                    no_star_games.append(fixture_info)
                    continue
                # Save fetched standings data to file
                save_standings_data(league_id, standings_data)
            league_standings_cache[league_id] = extract_team_info(standings_data)
        
        team_info = league_standings_cache.get(league_id)

        # If team info extraction fails, add to no_star_games and skip to next fixture
        if not team_info:
            print(f"No team info extracted for league {league_id}. Skipping fixture {fixture_id}.")
            fixture_info = {
                'fixture_data': fixture_data,
                'winning_team': None,
                'comment': "No team info extracted",
                'league_name': league_name,
                'warning': warning
            }
            no_star_games.append(fixture_info)
            continue

        home_team_rank = get_team_rank(team_info, home_team_name)
        away_team_rank = get_team_rank(team_info, away_team_name)

        # If rank data is missing, add to no_star_games and skip to next fixture
        if home_team_rank is None or away_team_rank is None:
            print(f"Rank data missing for fixture {fixture_id}. Skipping fixture {fixture_id}.")
            fixture_info = {
                'fixture_data': fixture_data,
                'winning_team': None,
                'comment': "Rank data missing",
                'league_name': league_name,
                'warning': warning
            }
            no_star_games.append(fixture_info)
            continue

        if abs(home_team_rank - away_team_rank) >= 4:
            predictions = fetch_data_with_rate_limit(get_fixture_prediction, fixture_id)
            if not predictions:
                print(f"No predictions available for fixture {fixture_id}. Skipping fixture {fixture_id}.")
                fixture_info = {
                    'fixture_data': fixture_data,
                    'winning_team': None,
                    'comment': "No predictions available",
                    'league_name': league_name,
                    'warning': warning
                }
                no_star_games.append(fixture_info)
                continue

            # Parse from team_info to selected team
            home_team_data = find_team_data_by_name(home_team_name, team_info)
            away_team_data = find_team_data_by_name(away_team_name, team_info)
            home_team_points, away_team_points, rating, winner_name, points_winner_name, comment = rate_fixture(predictions, home_team_data, away_team_data)
            home_team_warning = ""
            away_team_warning = ""
            home_team_injuries = []
            away_team_injuries = []
            home_team_players = []
            away_team_players = []

            # Fetch more data only for games rated one_star, two_star, or three_star
            if rating in {'three_star', 'two_star', 'one_star'}: 
                
                ## This hasnt ever returned anything, maybe it should only be used for major league games? ##


                ## I think this would be a good start for getting team data by teamId instead and passing the data to rate_fixture



                # home_team_players, away_team_players = fetch_data_with_rate_limit(get_player_data, fixture_id) 

                # if is_valid_data(home_team_players) and is_valid_data(away_team_players):
                #     home_team_injuries, away_team_injuries = fetch_data_with_rate_limit(get_injury_data, fixture_id) 
                #     home_team_key_players, away_team_key_players = get_key_players_by_team(home_team_players, away_team_players)

                #     # Check for injured key players
                #     if is_valid_data(home_team_key_players):
                #         for player in home_team_key_players:
                #             if any(injury['player'] == player['name'] for injury in home_team_injuries):
                #                 home_team_warning = "Warning: Home team key player injured!"
                #                 warning = home_team_warning
                #                 away_team_points -= 1
                #                 break

                #     if is_valid_data(away_team_key_players):
                #         for player in away_team_key_players:
                #             if any(injury['player'] == player['name'] for injury in away_team_injuries):
                #                 away_team_warning = "Warning: Away team key player injured!"
                #                 if warning is None:
                #                     warning = away_team_warning
                #                     away_team_points -= 1
                #                 break

                # Recalculate the rating after adjusting for injuries
                rating = determine_rating(home_team_points, away_team_points)
            
            fixture_info = {
                'fixture_data': fixture_data,
                'home_team_points': home_team_points,
                'away_team_points': away_team_points,
                'rating': rating,
                'winning_team': winner_name,
                'points_winner_name': points_winner_name,
                'comment': comment,
                'league_name': league_name,
                'warning': warning
            }

            if rating == 'three_star':
                three_star_games.append(fixture_info)
            elif rating == 'two_star':
                two_star_games.append(fixture_info)
            elif rating == 'one_star':
                one_star_games.append(fixture_info)
                
        else:
            print(f"Rank difference between {home_team_name} and {away_team_name} is 4 or less. Skipping fixture {fixture_id}.")
            fixture_info = {
                'fixture_data': fixture_data,
                'home_team_points': 0,
                'away_team_points': 0,
                'winning_team': None,
                'comment': "Rank difference too small to predict",
                'league_name': league_name,
                'warning': warning
            }
            no_star_games.append(fixture_info)

        save_rated_fixtures(one_star_games, two_star_games, three_star_games, no_star_games)
        one_star_games.clear()
        two_star_games.clear()
        three_star_games.clear()
        no_star_games.clear()
    
    print("\nThree Star Games:")
    for game in rated_fixtures['three_star_games']:
        print(f"Fixture: {game['fixture_data']['fixture']['id']}, "
              f"Home Team Points: {game['home_team_points']}, "
              f"Away Team Points: {game['away_team_points']}, "
              f"Points Winner: {game['points_winner_name']}, "
              f"Predicted Winner: {game['winning_team']}, "
              f"Comment: {game['comment']}, "
              f"League: {game['league_name']}, "
              f"Warning: {game['warning']}")

    print("\nTwo Star Games:")
    for game in rated_fixtures['two_star_games']:
        print(f"Fixture: {game['fixture_data']['fixture']['id']}, "
              f"Home Team Points: {game['home_team_points']}, "
              f"Away Team Points: {game['away_team_points']}, "
              f"Points Winner: {game['points_winner_name']}, "
              f"Predicted Winner: {game['winning_team']}, "
              f"Comment: {game['comment']}, "
              f"League: {game['league_name']}, "
              f"Warning: {game['warning']}")

    print("\nOne Star Games:")
    for game in rated_fixtures['one_star_games']:
        print(f"Fixture: {game['fixture_data']['fixture']['id']}, "
              f"Home Team Points: {game['home_team_points']}, "
              f"Away Team Points: {game['away_team_points']}, "
              f"Points Winner: {game['points_winner_name']}, "
              f"Predicted Winner: {game['winning_team']}, "
              f"Comment: {game['comment']}, "
              f"League: {game['league_name']}, "
              f"Warning: {game['warning']}")

    ## Implement something that saves currenct lists of one_star_games, two_star_games and three_star_games into a rated_fixtures.json
if __name__ == "__main__":
    main()
