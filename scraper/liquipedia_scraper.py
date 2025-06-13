import requests
from bs4 import BeautifulSoup
from .mongo_client import get_mongo_collection

def get_team_info(team_name):
    collection = get_mongo_collection()

    # 🔄 Supprimer les anciennes données si présentes
    collection.delete_one({"team": team_name})

    # 🌍 Scraping de la page League of Legends sur Liquipedia
    url = f"https://liquipedia.net/leagueoflegends/{team_name}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return [], {}, {}

    soup = BeautifulSoup(response.text, "html.parser")

    # 🔍 Extraction des joueurs dans la table .roster-card
    players = []
    table = soup.find("table", {"class": lambda c: c and "roster-card" in c})
    if table:
        rows = table.find_all("tr", class_="Player")
        for row in rows:
            pseudo_tag = row.find("td", class_="ID")
            pseudo = pseudo_tag.find("a").text.strip() if pseudo_tag else "Unknown"
            country_img = pseudo_tag.find("img", title=True) if pseudo_tag else None
            country = country_img['title'] if country_img else "Unknown"

            name_td = row.find("td", class_="Name")
            real_name = name_td.find("div", class_="LargeStuff").text.strip() if name_td else "Unknown"

            pos_td = row.find("td", class_="Position")
            role = pos_td.get_text(strip=True) if pos_td else "Unknown"

            date_td = row.find("td", class_="Date")
            join_date = date_td.get_text(strip=True) if date_td else "Unknown"

            players.append({
                "pseudo": pseudo,
                "name": real_name,
                "country": country,
                "role": role,
                "join_date": join_date
            })

    # 📊 Statistiques des joueurs
    stats = {
        "total_players": len(players),
        "countries": list(set(p["country"] for p in players)),
        "avg_name_length": round(sum(len(p["pseudo"]) for p in players) / len(players), 2) if players else 0
    }

    # 🧾 Infos générales depuis l’infobox
    info = {
        "location": None,
        "region": None,
        "coachs": [],
        "winnings": None,
        "created": None,
        "socials": []
    }

    infobox = soup.find("div", class_="fo-nttax-infobox")
    if infobox:
        rows = infobox.find_all("div", class_="infobox-cell-2")
        for row in rows:
            label = row.get_text(strip=True).lower()
            value_div = row.find_next_sibling("div")
            if not value_div:
                continue
            value = value_div.get_text(strip=True)

            if "location" in label:
                info["location"] = value
            elif "region" in label:
                info["region"] = value
            elif "coach" in label:
                links = value_div.find_all("a")
                info["coachs"] = [a.get_text(strip=True) for a in links]
            elif "winnings" in label:
                info["winnings"] = value
            elif "created" in label:
                info["created"] = value

        icons = infobox.find("div", class_="infobox-icons")
        if icons:
            social_links = icons.find_all("a", href=True)
            info["socials"] = [a["href"] for a in social_links if a["href"].startswith("http")]

    # 💾 Sauvegarde en base MongoDB
    collection.insert_one({
        "team": team_name,
        "players": players,
        "stats": stats,
        "info": info
    })

    return players, stats, info
