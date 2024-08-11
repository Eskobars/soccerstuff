import json
import os
import logging

from fetchers import fetch_match_predictions
from services.fetch_data import fetch_data_with_rate_limit
from config import PREDICTIONS_DIR

# Configure logging
logging.basicConfig(level=logging.INFO)

def is_data_up_to_date(filename):
    """
    Check if the data in the file is valid and not empty.
    
    :param filename: Path to the JSON file.
    :return: True if data is valid and not empty, False otherwise.
    """
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                return bool(data and 'response' in data and isinstance(data['response'], list) and len(data['response']) > 0)
        except (FileNotFoundError, KeyError, IndexError, ValueError, json.JSONDecodeError) as e:
            logging.error(f"Error reading data from {filename}: {e}")
            return False
    return False

def get_fixture_prediction(fixture_id):
    filename = os.path.join(PREDICTIONS_DIR, f'predictions_data_{fixture_id}.json')

    if is_data_up_to_date(filename):
        logging.info(f"Predictions data for fixture {fixture_id} is up to date, loading from file.")
        with open(filename, 'r') as f:
            predictions = json.load(f)
    else:
        logging.info(f"Fetching new predictions data for fixture {fixture_id}...")
        predictions = fetch_data_with_rate_limit(fetch_match_predictions, fixture_id)
        with open(filename, 'w') as f:
            json.dump(predictions, f, indent=4)
        logging.info("Predictions data fetched and stored successfully.")
    
    if predictions and 'response' in predictions and isinstance(predictions['response'], list) and len(predictions['response']) > 0:
        return predictions['response'][0]
    else:
        logging.warning(f"No predictions available or incorrect format for fixture {fixture_id}.")
        return {}

def rate_fixture(predictions, home_team_data, away_team_data):
    """
    Rate a fixture based on its prediction and return the points and rating for home and away teams,
    along with the winning team and comment.
    """
    default_comment = "No comments"
    
    try:
        # Initialize points for the home and away teams
        home_team_points = 0
        away_team_points = 0

        # Extract prediction data
        predictions_item = predictions.get('predictions', {})
        teams_item = predictions.get('teams', {})
        home_team_item = teams_item.get('home', {})
        away_team_item = teams_item.get('away', {})
        league_item = predictions.get('league', {})

        # Convert percentage values to integers
        percent_home = int(predictions_item.get('percent', {}).get('home', '0').strip('%'))
        percent_draw = int(predictions_item.get('percent', {}).get('draw', '0').strip('%'))
        percent_away = int(predictions_item.get('percent', {}).get('away', '0').strip('%'))

        home_team_id = int(home_team_item.get('id', 0))
        away_team_id = int(away_team_item.get('id', 0))
        league_id = int(league_item.get('id', 0))

        predicted_winner_name = predictions_item.get('winner', {}).get('name', 'Unknown')
        home_team_name = home_team_data.get('team_name', 'Unknown')
        away_team_name = away_team_data.get('team_name', 'Unknown')

        home_form = home_team_data.get('form', '')
        away_form = away_team_data.get('form', '')

        # Ensure form has at least five characters
        if not home_form or not away_form or len(home_form) < 5 or len(away_form) < 5:
            return 0, 0, 'no_star', "None", "None", "Not enough recent matches, skipping"

        # Calculate win/lose ratios and goal ratios
        home_team_win_ratio, away_team_win_ratio = get_team_win_lose_ratios(home_team_item, away_team_item)
        home_team_goal_ratio, away_team_goal_ratio = get_team_goals_ratios(home_team_item, away_team_item)
        rank_difference = get_team_rank_difference(home_team_data, away_team_data)
        win_ratio_difference = home_team_win_ratio - away_team_win_ratio
        goal_ratio_difference = home_team_goal_ratio - away_team_goal_ratio

        # Extract comment and advice
        winner_data = predictions_item.get('winner', {})
        comment = winner_data.get('comment', default_comment)
        advice = predictions.get('advice', default_comment)
        comment = f"{comment} {'| ' if comment and advice else ''}{advice}".strip() or default_comment

        # Add points based on percentage values
        home_team_points += calculate_percentage_points(percent_home, percent_draw)
        away_team_points += calculate_percentage_points(percent_away, percent_draw)

        # Adjust points based on the win/lose ratio difference
        home_team_points += adjust_points_based_on_ratio(win_ratio_difference, is_home=True)
        away_team_points += adjust_points_based_on_ratio(-win_ratio_difference, is_home=False)

        # Adjust points based on the goal ratio difference
        home_team_points += adjust_points_based_on_goal_ratio(goal_ratio_difference, is_home=True)
        away_team_points += adjust_points_based_on_goal_ratio(-goal_ratio_difference, is_home=False)

        # Adjust points based on rank difference
        home_team_points += adjust_points_based_on_rank(rank_difference, is_home=True)
        away_team_points += adjust_points_based_on_rank(-rank_difference, is_home=False)

        # Adjust points based on total goals and goals difference
        home_team_points += adjust_points_based_on_points_difference(home_team_data.get('points', 0), away_team_data.get('points', 0))
        away_team_points += adjust_points_based_on_points_difference(away_team_data.get('points', 0), home_team_data.get('points', 0))
        
        home_team_points += adjust_points_based_on_goals_diff(home_team_data.get('goalsDiff', 0))
        away_team_points += adjust_points_based_on_goals_diff(away_team_data.get('goalsDiff', 0), is_home=False)

        # Adjust points based on recent form
        home_team_points += adjust_points_based_on_form(home_form, is_home=True)
        away_team_points += adjust_points_based_on_form(away_form, is_home=False)

        # Determine the winning team based on points
        points_winner_name = determine_winner(home_team_points, away_team_points, home_team_name, away_team_name)

        # Determine rating
        rating = determine_rating(home_team_points, away_team_points)

        logging.info(f"Fixture: {home_team_name} vs {away_team_name}, Home Team Points: {home_team_points}, Away Team Points: {away_team_points}, Comment: {comment}")
        logging.info(f"Predicted Winner: {predicted_winner_name}, Winner in points: {points_winner_name}")

        return home_team_points, away_team_points, rating, predicted_winner_name, points_winner_name, comment

    except (KeyError, IndexError, ValueError) as e:
        logging.error(f"Error processing predictions: {e}")
        return 0, 0, 'no_star', "None", "None", "Error retrieving comment"

def calculate_percentage_points(percent, percent_draw):
    if percent >= 70:
        return 2
    elif percent >= 60:
        return 1
    elif percent >= 45 and percent_draw >= 45:
        return 0
    return 0

def adjust_points_based_on_ratio(ratio_difference, is_home):
    if ratio_difference >= 3:
        return 2 if is_home else 0
    elif ratio_difference >= 2:
        return 1 if is_home else 0
    elif ratio_difference >= 1:
        return 0 if is_home else 0
    elif ratio_difference <= -3:
        return 0 if is_home else 2
    elif ratio_difference <= -2:
        return 0 if is_home else 1
    return 0

def adjust_points_based_on_goal_ratio(goal_ratio_difference, is_home):
    if goal_ratio_difference >= 3:
        return 2 if is_home else -1
    elif goal_ratio_difference >= 2:
        return 1 if is_home else -1
    elif goal_ratio_difference >= 1:
        return 0
    elif goal_ratio_difference <= -2:
        return -1 if is_home else 1
    elif goal_ratio_difference <= -3:
        return -2 if is_home else 2
    return 0

def adjust_points_based_on_rank(rank_difference, is_home):
    if rank_difference >= 10:
        return 2 if is_home else 0
    elif rank_difference >= 5:
        return 1 if is_home else 0
    elif rank_difference <= -10:
        return 0 if is_home else 2
    elif rank_difference <= -5:
        return 0 if is_home else 1
    return 0

def adjust_points_based_on_points_difference(home_points, away_points):
    points_difference = home_points - away_points
    if points_difference >= 30:
        return 2
    elif points_difference >= 20:
        return 1
    elif points_difference >= 10:
        return 0
    return 0

def adjust_points_based_on_goals_diff(goals_diff, is_home=True):
    if goals_diff > 30:
        return 3 if is_home else 2
    elif goals_diff > 15:
        return 2 if is_home else 1
    elif goals_diff > 0:
        return 1 if is_home else 1
    elif goals_diff < 0:
        return -1 if is_home else -1
    return 0

def adjust_points_based_on_form(form, is_home=True):
    if form.endswith('WWWWW'):
        return 2 if is_home else 0
    elif form.endswith('WWW'):
        return 1 if is_home else 0
    elif form.endswith('LLLLL'):
        return -2 if is_home else 0
    elif form.endswith('LLL'):
        return -1 if is_home else 0
    return 0

def determine_winner(home_team_points, away_team_points, home_team_name, away_team_name):
    if home_team_points > away_team_points:
        return home_team_name
    elif away_team_points > home_team_points:
        return away_team_name
    else:
        return "Draw"

def determine_rating(home_team_points, away_team_points):
    points_difference = abs(home_team_points - away_team_points)
    if away_team_points > home_team_points:
        # Adjust rating if away team wins
        if points_difference > 6:
            return 'four_star'  # Example: give a higher rating if the away team wins by a large margin
        elif points_difference > 4:
            return 'three_star'
        elif points_difference > 2:
            return 'two_star'
        else:
            return 'one_star'
    else:
        # Original rating if the home team wins or it's a close game
        if points_difference > 6:
            return 'three_star'
        elif points_difference > 4:
            return 'two_star'
        elif points_difference > 2:
            return 'one_star'
        else:
            return 'no_star'

def calculate_win_lose_ratio(wins, losses):
    wins = int(wins)
    losses = int(losses)
    return wins / losses if losses > 0 else float('inf')

def get_team_win_lose_ratios(home_team_item, away_team_item):
    home_total_wins = home_team_item.get('league', {}).get('fixtures', {}).get('wins', {}).get('total', 0)
    home_total_losses = home_team_item.get('league', {}).get('fixtures', {}).get('loses', {}).get('total', 0)
    away_total_wins = away_team_item.get('league', {}).get('fixtures', {}).get('wins', {}).get('total', 0)
    away_total_losses = away_team_item.get('league', {}).get('fixtures', {}).get('loses', {}).get('total', 0)

    return calculate_win_lose_ratio(home_total_wins, home_total_losses), calculate_win_lose_ratio(away_total_wins, away_total_losses)

def get_team_goals_ratios(home_team_item, away_team_item):
    home_total_goals_for = home_team_item.get('league', {}).get('goals', {}).get('for', {}).get('total', {}).get('total', 0)
    home_total_goals_against = home_team_item.get('league', {}).get('goals', {}).get('against', {}).get('total', {}).get('total', 0)
    away_total_goals_for = away_team_item.get('league', {}).get('goals', {}).get('for', {}).get('total', {}).get('total', 0)
    away_total_goals_against = away_team_item.get('league', {}).get('goals', {}).get('against', {}).get('total', {}).get('total', 0)

    home_goals_ratio = home_total_goals_for / home_total_goals_against if home_total_goals_against > 0 else home_total_goals_for
    away_goals_ratio = away_total_goals_for / away_total_goals_against if away_total_goals_against > 0 else away_total_goals_for

    return home_goals_ratio, away_goals_ratio

def get_team_rank_difference(home_team_data, away_team_data):
    home_rank = home_team_data.get('rank', 0)
    away_rank = away_team_data.get('rank', 0)
    return away_rank - home_rank
