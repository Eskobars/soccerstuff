import os
import json
from services.fetch_data import fetch_data_with_rate_limit
from datetime import datetime
from services.fixtures import filter_fixtures, get_fixtures_data
from services.standings import get_standings_data, extract_team_info, get_team_rank
from services.injuries import get_injury_data
from services.predictions import rate_fixture, get_fixture_prediction, determine_rating
from services.players import get_player_data, get_key_players_by_team
from config import PREDICTIONS_DIR, INJURIES_DIR, PLAYERS_DIR, STANDINGS_DIR, RATINGS_DIR, TEAMS_DIR, BETS_DIR

# Create directories if they do not exist
os.makedirs(PREDICTIONS_DIR, exist_ok=True)
os.makedirs(INJURIES_DIR, exist_ok=True)
os.makedirs(PLAYERS_DIR, exist_ok=True)
os.makedirs(STANDINGS_DIR, exist_ok=True)
os.makedirs(RATINGS_DIR, exist_ok=True)
os.makedirs(TEAMS_DIR, exist_ok = True)

def save_bets(bets):
    """Save bets to a file."""
    file_path = os.path.join(BETS_DIR, 'bets.json')
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            existing_bets = json.load(file)
    else:
        existing_bets = []

    existing_bets.extend(bets)

    with open(file_path, 'w') as file:
        json.dump(existing_bets, file, indent=4)

def find_latest_file(directory):
    # Get the current date as a string in the format 'YYYY-MM-DD'
    current_date_str = datetime.now().strftime('%Y-%m-%d')
    
    # List all files in the directory that match the pattern
    files = [f for f in os.listdir(directory) if f.startswith('rated_fixtures_') and f.endswith('.json')]
    
    # Filter files that match the current date
    matching_files = [f for f in files if f[len('rated_fixtures_'): -len('.json')] == current_date_str]
    
    # Return the file if found, otherwise return None
    if matching_files:
        return matching_files[0]
    else:
        return None
    
# Helper function to determine if data is valid (not None and not empty)
def is_valid_data(data):
    return data is not None and len(data) > 0

# Function to find team data by team name
def find_team_data_by_name(team_name, team_info):
    for team in team_info:
        if team['team_name'] == team_name:
            return team
    return None

def load_standings_data(league_id):
    """Load standings data from a file and ensure it contains valid content."""
    file_path = os.path.join(STANDINGS_DIR, f'standings_{league_id}.json')
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                if data and 'response' in data and isinstance(data['response'], list) and len(data['response']) > 0:
                    return data
        except (FileNotFoundError, KeyError, IndexError, ValueError, json.JSONDecodeError) as e:
            print(f"Error reading standings data from {file_path}: {e}")
    
    return None

def save_standings_data(league_id, data):
    """Save standings data to a file."""
    file_path = os.path.join(STANDINGS_DIR, f'standings_{league_id}.json')
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

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

    # Initialize counters
    total_games_processed = 0
    games_rated = 0
    games_skipped = 0

    all_fixtures_data = fetch_data_with_rate_limit(get_fixtures_data)

    filtered_fixtures = filter_fixtures(all_fixtures_data, statuses_to_search, trusted_countries)

    for fixture_data in filtered_fixtures:

        total_games_processed += 1  # Increment total games processed
        fixture_id = fixture_data['fixture']['id']
        if fixture_id in processed_fixture_ids:
            games_skipped += 1  # Increment skipped games
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
            games_skipped += 1  # Increment skipped games
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
                    games_skipped += 1  # Increment skipped games
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
            games_skipped += 1  # Increment skipped games
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
            games_skipped += 1  # Increment skipped games
            continue

        if abs(home_team_rank - away_team_rank) >= 4:
            predictions = get_fixture_prediction(fixture_id)
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
                games_skipped += 1  # Increment skipped games
                continue

            # Parse from team_info to selected team
            home_team_data = find_team_data_by_name(home_team_name, team_info)
            away_team_data = find_team_data_by_name(away_team_name, team_info)
            home_team_points, away_team_points, rating, winner_name, points_winner_name, comment = rate_fixture(predictions, home_team_data, away_team_data)

            # Recalculate the rating after adjusting for injuries (if applicable)
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

            games_rated += 1  # Increment rated games
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
            games_skipped += 1  # Increment skipped games

        save_rated_fixtures(one_star_games, two_star_games, three_star_games, no_star_games)
        one_star_games.clear()
        two_star_games.clear()
        three_star_games.clear()
        no_star_games.clear()
    
    load_rated_fixtures()

    all_games = {
        'three_star_games': rated_fixtures['three_star_games'],
        'two_star_games': rated_fixtures['two_star_games'],
        'one_star_games': rated_fixtures['one_star_games']
    }

    # Combine all games into a single list and keep track of indices
    indexed_games = []
    index_counter = 1

    print("\nThree Star Games:")
    for game in rated_fixtures['three_star_games']:
        print(f"{index_counter}: {game['fixture_data']['teams']['home']['name']} vs {game['fixture_data']['teams']['away']['name']}, "
            f"Home Team Points: {game['home_team_points']}, "
            f"Away Team Points: {game['away_team_points']}, "
            f"Predicted Winner: {game['winning_team']}, "
            f"Comment: {game['comment']}, "
            f"League: {game['league_name']}, "
            f"Warning: {game['warning']}")
        indexed_games.append(game)
        index_counter += 1

    print("\nTwo Star Games:")
    for game in rated_fixtures['two_star_games']:
        print(f"{index_counter}: {game['fixture_data']['teams']['home']['name']} vs {game['fixture_data']['teams']['away']['name']}, "
            f"Home Team Points: {game['home_team_points']}, "
            f"Away Team Points: {game['away_team_points']}, "
            f"Predicted Winner: {game['winning_team']}, "
            f"Comment: {game['comment']}, "
            f"League: {game['league_name']}, "
            f"Warning: {game['warning']}")
        indexed_games.append(game)
        index_counter += 1

    print("\nOne Star Games:")
    for game in rated_fixtures['one_star_games']:
        print(f"{index_counter}: {game['fixture_data']['teams']['home']['name']} vs {game['fixture_data']['teams']['away']['name']}, "
            f"Home Team Points: {game['home_team_points']}, "
            f"Away Team Points: {game['away_team_points']}, "
            f"Predicted Winner: {game['winning_team']}, "
            f"Comment: {game['comment']}, "
            f"League: {game['league_name']}, "
            f"Warning: {game['warning']}")
        indexed_games.append(game)
        index_counter += 1

    print(f"Total games processed: {total_games_processed}")
    print(f"Total games rated: {games_rated}")
    print(f"Total games skipped: {games_skipped}")

    # Ask user if they want to save any bets
    bets = []
    while True:
        save_bet = input("\nWould you like to save a bet? ((yes (y) / no (n)): ").strip().lower()
        if save_bet in ['no', 'n']:
            break
        if save_bet in ['yes', 'y']:
            try:
                game_number = int(input("Enter the game number: ").strip())
                if 1 <= game_number < index_counter:
                    selected_fixture = indexed_games[game_number - 1]
                    multiplier = float(input("Enter the multiplier: ").strip())

                    # Save the bet with the selected fixture's points
                    bet = {
                        'team_name': f"{game['fixture_data']['teams']['home']['name']} vs {game['fixture_data']['teams']['away']['name']}",
                        'multiplier': multiplier,
                        'home_team_points': selected_fixture['home_team_points'],
                        'away_team_points': selected_fixture['away_team_points'],
                        'predicted_winner' : f"Predicted winner: {game['winning_team']}",
                    }
                    bets.append(bet)
                else:
                    print("Invalid game number.")
            except ValueError:
                print("Invalid input. Please enter a valid number.")

    if bets:
        save_bets(bets)
        print("Bets have been saved.")
    else:
        print("No bets were saved.")

if __name__ == "__main__":
    main()
