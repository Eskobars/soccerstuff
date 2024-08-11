def find_team_data_by_name(team_name, team_info):
    for team in team_info:
        if team['team_name'] == team_name:
            return team
    return None