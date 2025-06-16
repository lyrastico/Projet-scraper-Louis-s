import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from .mongo_client import get_mongo_collection


def get_match_info(match_html):
    entries = match_html.find_all('div', class_='brkts-opponent-entry')
    teams, scores = [], []
    for e in entries:
        name_el = e.find('span', class_='name') or e.find('span', class_='visible-xs')
        team = name_el.text.strip() if name_el else "Inconnu"
        score_el = e.find('div', class_='brkts-opponent-score-inner')
        score = int(score_el.text.strip()) if score_el and score_el.text.strip().isdigit() else 0
        teams.append(team)
        scores.append(score)
    if len(teams) == 2:
        winner = teams[0] if scores[0] > scores[1] else teams[1] if scores[1] > scores[0] else "Égalité"
        return {
            'team1': teams[0],
            'score1': scores[0],
            'team2': teams[1],
            'score2': scores[1],
            'winner': winner
        }
    return None

def get_match_id(match_html):
    popup = match_html.find('div', class_='brkts-popup-body-element')
    link = popup.select_one('a[href*="Match:ID"]')
    if link:
        match_id = link['href'].split('/')[-1]
        return match_id
    return None


def scrape_tournament_matches(url):
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        matches = soup.find_all('div', class_='brkts-match')
        match_data = []
        for match in matches:
            match_info = get_match_info(match)
            if match_info:
                match_id = get_match_id(match)
                match_info['match_id'] = match_id
                match_data.append(match_info)
        return match_data
    except Exception as e:
        print(f"Erreur lors du scraping : {e}")
        return []


def main():
    collection = get_mongo_collection("matchs")
    if collection is None:
        print("Erreur : collection MongoDB introuvable.")
        return

    try:
        collection.delete_many({})
        print("🗑 Anciennes données supprimées de la collection 'matchs'.\n")
    except Exception as e:
        print(f"Erreur de suppression de données : {e}")
        return

    total = 0
    urls = []

    for year in range(2020, 2026):
        for season in ["Winter", "Spring", "Summer"]:
            urls.append((f"https://liquipedia.net/leagueoflegends/LEC/{year}/{season}/Playoffs", f"LEC {season} {year}"))
        urls.append((f"https://liquipedia.net/leagueoflegends/Mid-Season_Invitational/{year}", f"MSI {year}"))
        urls.append((f"https://liquipedia.net/leagueoflegends/World_Championship/{year}", f"Worlds {year}"))

    for url, tournament_name in urls:
        print(f"Traitement : {tournament_name}")
        matches = scrape_tournament_matches(url)

        if not matches: 
            print("Aucun match trouvé pour ce tournoi.\n")
            continue

        for m in matches:
            m['tournament'] = tournament_name

        try:
            collection.insert_many(matches)
            print(f"{len(matches)} match(s) inséré(s).\n")
            total += len(matches)
        except Exception as e:
            print(f"Erreur d'insertion de données : {e}")

    print(f"Total : {total} match(s) extraits depuis 2020.")
