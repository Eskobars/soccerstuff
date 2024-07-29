import json
import os

from services.fixtures import filter_fixtures, get_fixtures_data
from services.standings import get_standings_data, extract_team_info, get_team_rank
from services.injuries import get_injury_data
from services.predictions import rate_fixture, get_fixture_prediction
from services.players import get_player_data
from config import PREDICTIONS_DIR, INJURIES_DIR, PLAYERS_DIR, STANDINGS_DIR

# Create directories if they do not exist
os.makedirs(PREDICTIONS_DIR, exist_ok=True)
os.makedirs(INJURIES_DIR, exist_ok=True)
os.makedirs(PLAYERS_DIR, exist_ok=True)
os.makedirs(STANDINGS_DIR, exist_ok=True)

def main():
    print("Loading...")
    statuses_to_search = ['NS', 'TBD']
    leagues = ['Ykkönen', 'Kolmonen', 'Kakkonen', 'Liga Profesional Argentina', 'Serie B', 'Serie A', 'Super League']
    one_star_games = []
    two_star_games = []
    three_star_games = []

    # Get or use existing .json fixture data for the day
    all_fixtures_data = get_fixtures_data()

    # Filter fixtures by status and league
    filtered_fixtures = filter_fixtures(all_fixtures_data, leagues, statuses_to_search)

    for fixture_data in filtered_fixtures:
        fixture_id = fixture_data['fixture']['id']
        league_name = fixture_data['league']['name']
        league_id = fixture_data['league']['id']
        home_team_name = fixture_data['teams']['home']['name']
        away_team_name = fixture_data['teams']['away']['name']
        
        # Fetch league rank info 
        team_ranks_data = get_standings_data(league_id)
        team_info = extract_team_info(team_ranks_data)
        
        # Get ranks for home and away teams
        home_team_rank = get_team_rank(team_info, home_team_name)
        away_team_rank = get_team_rank(team_info, away_team_name)
        
        warning = ""
        # Check rank difference
        if ((home_team_rank + 5 > away_team_rank) or (away_team_rank + 5 > home_team_rank)):
            predictions = get_fixture_prediction(fixture_id)
            if not predictions:
                print(f"No predictions available for fixture {fixture_id}. Skipping.")
                continue
            
            rating, winning_team, comment = rate_fixture(predictions, team_info)

            # Fetch injury and player data
            home_team_injuries, away_team_injuries = get_injury_data(fixture_id)
            home_team_players, away_team_players = get_player_data(fixture_id)

            # Check for injured key players
            home_team_warning = ""
            away_team_warning = ""

            if home_team_players:
                for player in home_team_players:
                    if any(injury['player'] == player['name'] for injury in home_team_injuries):
                        home_team_warning = "Warning: Key player injured!"
                        warning = home_team_warning
                        break

            if away_team_players:
                for player in away_team_players:
                    if any(injury['player'] == player['name'] for injury in away_team_injuries):
                        away_team_warning = "Warning: Key player injured!"
                        warning = away_team_warning
                        break

            # Include the fixture data along with rating, winning team, comment, and warning
            fixture_info = {
                'fixture_data': fixture_data,
                'winning_team': winning_team,
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
            print(f"Rank difference between {home_team_name} and {away_team_name} is 5 or less. Skipping prediction for fixture {fixture_id}.")
            # Set rating to 'no_star' and skip further processing
            fixture_info = {
                'fixture_data': fixture_data,
                'winning_team': None,
                'comment': "Rank difference too small to predict",
                'league_name': league_name,
                'warning': warning
            }
            # No need to append to the categorized lists, as it's rated 'no_star'
    
    # Print categorized games
    print("\nThree Star Games:")
    for game in three_star_games:
        print(f"Fixture: {game['fixture_data']['fixture']['id']}, Winner: {game['winning_team']}, Comment: {game['comment']}, League: {game['league_name']}, Warning: {game['warning']}")

    print("\nTwo Star Games:")
    for game in two_star_games:
        print(f"Fixture: {game['fixture_data']['fixture']['id']}, Winner: {game['winning_team']}, Comment: {game['comment']}, League: {game['league_name']}, Warning: {game['warning']}")

    print("\nOne Star Games:")
    for game in one_star_games:
        print(f"Fixture: {game['fixture_data']['fixture']['id']}, Winner: {game['winning_team']}, Comment: {game['comment']}, League: {game['league_name']}, Warning: {game['warning']}")

if __name__ == "__main__":
    main()