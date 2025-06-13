import requests
from bs4 import BeautifulSoup
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
        return {'team1': teams[0], 'score1': scores[0], 'team2': teams[1], 'score2': scores[1]}
    return None

def scrape_tournament_matches(url):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    return [m for m in (get_match_info(m) for m in soup.find_all('div', class_='brkts-match')) if m]

def main():
    collection = get_mongo_collection("matchs")
    if collection is None:
        print("❌ Erreur : collection MongoDB introuvable.")
        return

    collection.delete_many({})
    print("🗑 Anciennes données supprimées de la collection 'matchs'.\n")

    total = 0

    # 🏆 Génère toutes les URLs LEC Playoffs + MSI + Worlds
    urls = []

    for year in range(2020, 2026):
        for season in ["Winter", "Spring", "Summer"]:
            urls.append((f"https://liquipedia.net/leagueoflegends/LEC/{year}/{season}/Playoffs", f"LEC {season} {year}"))

        urls.append((f"https://liquipedia.net/leagueoflegends/Mid-Season_Invitational/{year}", f"MSI {year}"))
        urls.append((f"https://liquipedia.net/leagueoflegends/World_Championship/{year}", f"Worlds {year}"))

    # 🔍 Scraping
    for url, tournament_name in urls:
        print(f"🔍 Traitement : {tournament_name}")
        matches = scrape_tournament_matches(url)

        if not matches:
            print("⚠️ Aucun match trouvé pour ce tournoi.\n")
            continue

        for m in matches:
            m['tournament'] = tournament_name

        collection.insert_many(matches)
        print(f"✅ {len(matches)} match(s) inséré(s).\n")
        total += len(matches)

    print(f"📊 Total : {total} match(s) extraits depuis 2020.")
