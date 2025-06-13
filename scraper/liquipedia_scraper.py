import requests
from bs4 import BeautifulSoup
from .mongo_client import get_mongo_collection

def get_team_info(team_name):
    collection = get_mongo_collection()
    cached = collection.find_one({"team": team_name})
    if cached:
        return cached["players"], cached.get("stats", {})

    url = f"https://liquipedia.net/valorant/{team_name}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return [], {}

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", class_="wikitable")
    if not table:
        return [], {}

    players = []
    rows = table.find_all("tr")[1:]
    for row in rows:
        cells = row.find_all("td")
        if not cells or len(cells) < 1:
            continue

        # Nom
        name = cells[0].get_text(strip=True)

        # Pays
        country_img = row.find("img", title=True)
        country = country_img['title'] if country_img else "Unknown"

        # Rôle (s'il existe)
        role = "Unknown"
        if len(cells) > 1:
            role_text = cells[1].get_text(strip=True)
            if role_text:
                role = role_text

        players.append({
            "name": name,
            "country": country,
            "role": role
        })

    stats = {
        "total_players": len(players),
        "countries": list(set(p["country"] for p in players)),
        "avg_name_length": round(sum(len(p["name"]) for p in players) / len(players), 2) if players else 0
    }

    collection.insert_one({
        "team": team_name,
        "players": players,
        "stats": stats
    })

    return players, stats
