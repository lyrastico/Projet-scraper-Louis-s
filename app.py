from flask import Flask, render_template, request, redirect, url_for
from scraper.liquipedia_scraper import get_team_info
from scraper.mongo_client import get_mongo_collection
from scraper.liquipedia_playoffs_scraper import main as load_match_data

app = Flask(__name__)

@app.route("/")
def home():
    collection = get_mongo_collection()
    team_names = collection.distinct("team")
    return render_template("index.html", team_names=team_names)

@app.route('/team', methods=['GET'])
def team():
    name = request.args.get('name')
    players, stats, info = get_team_info(name)
    return render_template('team.html', team=name, players=players, stats=stats, info=info)

@app.route('/compare', methods=['GET'])
def compare():
    team1 = request.args.get('team1')
    team2 = request.args.get('team2')

    if not team1 or not team2:
        return "Veuillez spécifier deux équipes avec ?team1=...&team2=...", 400

    players1, stats1, info1 = get_team_info(team1)
    players2, stats2, info2 = get_team_info(team2)

    # 🔍 Recherche des matchs entre team1 et team2
    collection = get_mongo_collection("matchs")
    matchups = list(collection.find({
        "$or": [
            {"team1": team1, "team2": team2},
            {"team1": team2, "team2": team1}
        ]
    }))

    print(f"📊 {len(matchups)} match(s) trouvé(s) entre {team1} et {team2}:")
    for match in matchups:
        print(f" - 🏆 {match.get('tournament', 'Inconnu')} : {match['team1']} {match['score1']} - {match['score2']} {match['team2']}")

    return render_template(
        'compare.html',
        team1=team1,
        team2=team2,
        stats1=stats1,
        stats2=stats2,
        info1=info1,
        info2=info2,
        matchups=matchups
    )

@app.route('/load_matches', methods=['POST'])
def load_matches():
    load_match_data()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
