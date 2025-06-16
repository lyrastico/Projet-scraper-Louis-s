import requests
import time
from bs4 import BeautifulSoup
from pymongo import MongoClient
from mongo_client import get_mongo_collection
import random


def get_match_details(match_id):
    url = f"https://liquipedia.net/leagueoflegends/{match_id}"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        games = soup.find_all('div', class_='match-bm')
        match_details = []
        for game in games:
            game_details = {}
            game_details['game_number'] = game.find('span', class_='mw-headline').text.strip().split(' ')[-1]
            teams = game.find_all('div', class_='match-bm-team')
            game_details['teams'] = []
            picks_bans = game.find('div', class_='match-bm/smatch-bm-picks-bans')
            if picks_bans:
                teams_picks = picks_bans.find_all('div', class_='brkts-popup-spaced')
                picks = []
                bans = []
                for team_picks in teams_picks:
                    team_picks_list = team_picks.find_all('div', class_='brkts-popup-element')
                    team_picks_champions = [img['title'] for img in team_picks_list if img.find('img')]
                    if 'Ban' in team_picks.text:
                        bans.append(team_picks_champions)
                    else:
                        picks.append(team_picks_champions)
                game_details['picks'] = picks
                game_details['bans'] = bans
            for team in teams:
                team_details = {}
                players = team.find_all('div', class_='match-bm-players-player')
                team_details['players'] = []
                for player in players:
                    player_details = {}
                    player_details['champion'] = player.find('a', title=True)['title']
                    player_details['name'] = player.find('a', href=True).text.strip()
                    player_details['role'] = player.find('div', class_='match-bm-players-player-role').find('img')['title']
                    loadout = player.find('div', class_='match-bm-lol-players-player-loadout')
                    player_details['summoner_spells'] = [img['title'] for img in loadout.find_all('img', title=True)[:2]]
                    player_details['items'] = [img['title'] for img in loadout.find_all('img', title=True)[2:]]
                    stats = player.find('div', class_='match-bm-players-player-stats')
                    player_details['kda'] = stats.find('div', class_='match-bm-players-player-stat-data').text.strip()
                    player_details['cs'] = stats.find_all('div', class_='match-bm-players-player-stat-data')[1].text.strip()
                    player_details['gold'] = stats.find_all('div', class_='match-bm-players-player-stat-data')[2].text.strip()
                    player_details['damage'] = stats.find_all('div', class_='match-bm-players-player-stat-data')[3].text.strip()
                    team_details['players'].append(player_details)
                team_details['name'] = team.find('div', class_='match-bm-team-header').find('a').text.strip()
                game_details['teams'].append(team_details)
            game_details['winner'] = game.find('div', class_='match-bm-team-highlighted').find('a').text.strip()
            match_details.append(game_details)
        return match_details
    except Exception as e:
        print(f"Erreur lors de la récupération des détails du match {match_id} : {e}")
        return None

def main():
    matchs_collection = get_mongo_collection("matchs")
    games_collection = get_mongo_collection("games")
    if matchs_collection is None or games_collection is None:
        print("Erreur : collection MongoDB introuvable.")
        return

    match_ids = matchs_collection.distinct('match_id')
    for match_id in match_ids:
        print(f"🔍 Traitement : {match_id}")
        match_details = get_match_details(match_id)
        if match_details:
            for game in match_details:
                game_data = {
                    'match_id': match_id,
                    'game_number': game['game_number'],
                    'teams': [team['name'] for team in game['teams']],
                    'winner': game['winner'],
                    'picks': game.get('picks', []),
                    'bans': game.get('bans', []),
                    'players': [{'name': player['name'], 'champion': player['champion'], 'role': player['role'], 'kda': player['kda'], 'cs': player['cs'], 'gold': player['gold'], 'damage': player['damage']} for team in game['teams'] for player in team['players']]
                }
                try:
                    games_collection.insert_one(game_data)
                    print(f"Données du jeu {game['game_number']} du match {match_id} insérées.")
                except Exception as e:
                    print(f"Erreur lors de l'insertion des données du jeu {game['game_number']} du match {match_id} : {e}")
        time.sleep(1)

if __name__ == "__main__":
    main()
