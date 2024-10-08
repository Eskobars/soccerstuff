import os

from services.fixtures import filter_fixtures, get_fixtures_data, load_rated_fixtures, save_rated_fixtures
from services.standings import get_standings_data, extract_team_info, get_team_rank
from services.predictions import rate_fixture, get_fixture_prediction, determine_rating
from services.bets import save_bets, load_saved_bets, check_bets_success_rate
from services.players import get_key_players_by_team, get_player_data
from services.injuries import filter_injuries_by_player_ids, get_injury_data
from helpers.data.find_team_data import find_team_data_by_name
from helpers.data.standings_data import save_standings_data, load_standings_data

from config import PREDICTIONS_DIR, INJURIES_DIR, PLAYERS_DIR, STANDINGS_DIR, RATINGS_DIR, TEAMS_DIR, BETS_DIR

# Create directories if they do not exist
os.makedirs(PREDICTIONS_DIR, exist_ok=True)
os.makedirs(INJURIES_DIR, exist_ok=True)
os.makedirs(PLAYERS_DIR, exist_ok=True)
os.makedirs(STANDINGS_DIR, exist_ok=True)
os.makedirs(RATINGS_DIR, exist_ok=True)
os.makedirs(TEAMS_DIR, exist_ok=True)
os.makedirs(BETS_DIR, exist_ok=True)

def main():
    print("Loading...")

    statuses_to_search = ['NS', 'TBD']
    trusted_leagues = {
        'Allsvenskan', 'Ettan - Norra', 'Ettan - S\u00f6dra', 'Superettan', 'Primera B', 'Primeira Liga', 'Eliteserien',  'Eredivisie',
        'Primera Divisi\u00f3n RFEF - Group 1', 'Primera Divisi\u00f3n RFEF - Group 2', 'Ligue 1', '2. Bundesliga', 'Bundesliga', 'Serie A', 'Serie B',
        'La Liga', 'Segunda Divisi\u00f3n', 'Championship', 'Premier League'
    }

    trusted_countries = {
        'England', 'Spain', 'Italy', 'Germany', 'France', 'Portugal', 'Netherlands', 'Sweden', 'Norway'
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
    failed_league_ids = set()

    total_games_processed = 0
    games_rated = 0
    games_skipped = 0

    all_fixtures_data = get_fixtures_data()
    filtered_fixtures = filter_fixtures(all_fixtures_data, statuses_to_search, trusted_countries)

    for fixture_data in filtered_fixtures:
        total_games_processed += 1
        fixture_id = fixture_data['fixture']['id']
        if fixture_id in processed_fixture_ids:
            games_skipped += 1
            
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
            games_skipped += 1  

            continue

        # Check if standings data is already cached or in files
        if league_id not in league_standings_cache:
            standings_data = load_standings_data(league_id)
            if not standings_data:
                standings_data = get_standings_data(league_id)
                if not standings_data or not standings_data.get('response'):
                    print(f"Standings data is empty or invalid for league {league_id}. Skipping fixture {fixture_id}.")
                    failed_league_ids.add(league_id)

                    fixture_info = {
                        'fixture_data': fixture_data,
                        'winning_team': None,
                        'comment': "No standings data available",
                        'league_name': league_name,
                        'warning': warning
                    }
                    no_star_games.append(fixture_info)
                    games_skipped += 1

                    continue
                save_standings_data(league_id, standings_data)
            league_standings_cache[league_id] = extract_team_info(standings_data)
        
        team_info = league_standings_cache.get(league_id)

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
            games_skipped += 1

            continue

        home_team_rank = get_team_rank(team_info, home_team_name)
        away_team_rank = get_team_rank(team_info, away_team_name)

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
            games_skipped += 1

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
                games_skipped += 1

                continue

            home_team_data = find_team_data_by_name(home_team_name, team_info)
            away_team_data = find_team_data_by_name(away_team_name, team_info)
            home_team_points, away_team_points, rating, winner_name, points_winner_name, comment = rate_fixture(predictions, home_team_data, away_team_data)

            # Recalculate the rating after adjusting for injuries (TODO)
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
            games_rated += 1
            
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
            games_skipped += 1

        save_rated_fixtures(one_star_games, two_star_games, three_star_games, no_star_games)

    rated_fixtures = load_rated_fixtures()

    # all_games = {
    #     'three_star_games': rated_fixtures['three_star_games'],
    #     'two_star_games': rated_fixtures['two_star_games'],
    #     'one_star_games': rated_fixtures['one_star_games']
    # }

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

    # This loop handles retrieving injury data for selected matches
    while True:
        get_injuries = input("\nWould you like to get injury data for any game? (yes (y) / no (n)): ").strip().lower()
        if get_injuries in ['no', 'n']:
            break
        if get_injuries in ['yes', 'y']:
            try:
                game_number = int(input("Enter the game number: ").strip())
                if 1 <= game_number < index_counter:
                    selected_fixture = indexed_games[game_number - 1]
                    fixture_id = selected_fixture['fixture_data']['fixture']['id']

                    # Fetch the player data for the home and away teams
                    players_home, players_away = get_player_data(fixture_id)

                    # Determine the key players for both teams
                    key_players_home, key_players_away = get_key_players_by_team(players_home, players_away)

                    # Extract the player IDs from the key players for filtering injuries
                    key_player_ids_home = {player['id'] for player in key_players_home}
                    key_player_ids_away = {player['id'] for player in key_players_away}

                    # Fetch injury data for the fixture
                    home_injuries, away_injuries = get_injury_data(fixture_id)

                    # Filter injuries to include only key players' injuries
                    key_home_injuries = filter_injuries_by_player_ids({'response': home_injuries}, key_player_ids_home)
                    key_away_injuries = filter_injuries_by_player_ids({'response': away_injuries}, key_player_ids_away)

                    # Print injury information for the home team
                    print(f"Injuries for {selected_fixture['fixture_data']['teams']['home']['name']}:")
                    for injury in key_home_injuries:  # key_home_injuries now contains full injury data
                        player = injury['player']
                        print(f"- {player['name']} ({player['position']}) - {injury['type']} - {injury['status']}")

                    # Print injury information for the away team
                    print(f"Injuries for {selected_fixture['fixture_data']['teams']['away']['name']}:")
                    for injury in key_away_injuries:  # key_away_injuries now contains full injury data
                        player = injury['player']
                        print(f"- {player['name']} ({player['position']}) - {injury['type']} - {injury['status']}")
                else:
                    print("Invalid game number.")
            except ValueError:
                print("Please enter a valid number.")
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")

    # This loop handles saving bets for selected matches
    bets = []
    while True:
        save_bet = input("\nWould you like to save a bet? (yes (y) / no (n)): ").strip().lower()
        if save_bet in ['no', 'n']:
            break
        if save_bet in ['yes', 'y']:
            try:
                game_number = int(input("Enter the game number: ").strip())
                if 1 <= game_number < index_counter:
                    selected_fixture = indexed_games[game_number - 1]
                    multiplier = float(input("Enter the multiplier: ").strip())

                    bet = {
                        'fixture_id': selected_fixture['fixture_data']['fixture']['id'],
                        'team_name': f"{selected_fixture['fixture_data']['teams']['home']['name']} vs {selected_fixture['fixture_data']['teams']['away']['name']}",
                        'multiplier': multiplier,
                        'home_team_points': selected_fixture['home_team_points'],
                        'away_team_points': selected_fixture['away_team_points'],
                        'predicted_winner': f"Predicted winner: {selected_fixture['winning_team']}"
                    }
                    bets.append(bet)
                else:
                    print("Invalid game number.")
            except ValueError:
                print("Invalid input. Please enter a valid number.")

    # Save the bets if there are any
    if bets:
        save_bets(bets)
        print("Bets have been saved.")
    else:
        print("No bets were saved.")

    while True:
        check_bets = input("\nWould you like to check the percentage of successful bets? (yes (y) / no (n)): ").strip().lower()
        if check_bets in ['no', 'n']:
            break
        if check_bets in ['yes', 'y']:
            bets = load_saved_bets() 
            check_bets_success_rate(bets)
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")

if __name__ == "__main__":
    main()
