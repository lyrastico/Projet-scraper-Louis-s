from flask import Flask, render_template, request
from scraper.liquipedia_scraper import get_team_info

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/team', methods=['GET'])
def team():
    name = request.args.get('name')
    players, stats = get_team_info(name)
    return render_template('team.html', team=name, players=players, stats=stats)

if __name__ == '__main__':
    app.run(debug=True)
