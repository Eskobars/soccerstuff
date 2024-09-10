## Info
This project is a simplistic betting assistant made with python for training purposes. 

Football.api provided endpoints.


## Setup
Clone repository and create config.py in root folder. It should look something like this:

```
import os
import sys

## You can get this by signing into https://dashboard.api-football.com/
API_KEY = 'YOUR API KEY' 
BASE_URL = 'v3.football.api-sports.io'

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.join(sys._MEIPASS, 'data')
else:
    BASE_DIR = os.path.join(os.path.dirname(__file__), 'data')

PREDICTIONS_DIR = os.path.join(BASE_DIR, 'predictions_data')
INJURIES_DIR = os.path.join(BASE_DIR, 'injuries_data')
PLAYERS_DIR = os.path.join(BASE_DIR, 'players_data')
STANDINGS_DIR = os.path.join(BASE_DIR, 'standings_data')
FIXTURES_DIR = os.path.join(BASE_DIR, 'fixtures_data')
RATINGS_DIR = os.path.join(BASE_DIR, 'rated_fixtures_data')
TEAMS_DIR = os.path.join(BASE_DIR, 'teams_data')
BETS_DIR = os.path.join(BASE_DIR, 'bets_data')
```
