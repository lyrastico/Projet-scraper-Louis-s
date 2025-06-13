import requests
from bs4 import BeautifulSoup
from mongo_client import get_mongo_collection

def get_match_info(match_html):
    """
    Récupère les informations d'un seul match depuis l'HTML fourni
    :param match_html: HTML du match à analyser
    :return: Dictionnaire avec les équipes et leurs scores
    """
    team_entries = match_html.find_all('div', class_='brkts-opponent-entry')
    
    teams = []
    scores = []
    
    for entry in team_entries:
        team_name_element = entry.find('span', class_='name')
        if not team_name_element:
            team_name_element = entry.find('span', {'class': 'visible-xs'})
            
        team_name = team_name_element.text.strip()
        
        score_element = entry.find('div', class_='brkts-opponent-score-inner')
        score = int(score_element.text) if score_element else 0
        
        teams.append(team_name)
        scores.append(score)
    
    return {
        'team1': teams[0],
        'score1': scores[0],
        'team2': teams[1],
        'score2': scores[1]
    }

def scrape_tournament_matches(url):
    """
    Récupère tous les matchs d'un tournoi
    :param url: URL de la page Liquipedia du tournoi
    :return: Liste des matchs avec leurs informations
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    matches_html = soup.find_all('div', class_='brkts-match')
    
    matches_info = []
    for match in matches_html:
        match_info = get_match_info(match)
        if match_info:
            matches_info.append(match_info)
    
    return matches_info

def main():
    from pymongo import MongoClient
    tournament_urls = [
        "https://liquipedia.net/leagueoflegends/LEC/2023/Winter/Playoffs",
        "https://liquipedia.net/leagueoflegends/LEC/2023/Spring/Playoffs",
        "https://liquipedia.net/leagueoflegends/LEC/2023/Summer/Playoffs",
        "https://liquipedia.net/leagueoflegends/LEC/2024/Winter/Playoffs",
        "https://liquipedia.net/leagueoflegends/LEC/2024/Spring/Playoffs",
        "https://liquipedia.net/leagueoflegends/LEC/2024/Summer/Playoffs",
        "https://liquipedia.net/leagueoflegends/LEC/2025/Winter/Playoffs",
        "https://liquipedia.net/leagueoflegends/LEC/2025/Spring/Playoffs"
    ]

    collection = get_mongo_collection("matchs") 
    
    if collection is None:
        print("Erreur : collection MongoDB introuvable.")
        return

    collection.delete_many({})
    print("Anciennes données supprimées de la collection 'matchs'.\n")

    for url in tournament_urls:
        parts = url.split('/')
        year = parts[4]
        season = parts[5]
        tournament_name = f"LEC {season} {year}"
        
        print(f"Processing: {tournament_name}")
        
        matches = scrape_tournament_matches(url)

        if not matches:
            print("Aucun match trouvé pour ce tournoi.")
            continue
        
        for match in matches:
            match['tournament'] = tournament_name

        collection.insert_many(matches)
        print(f"{len(matches)} match(s) inséré(s) dans MongoDB.\n")


if __name__ == "__main__":
    main()