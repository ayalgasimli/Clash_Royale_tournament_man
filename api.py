from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)  # This allows your HTML file to talk to this server

# --- CONFIGURATION ---
# GET YOUR KEY FROM: https://developer.clashroyale.com
CR_API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjY1NDNjZjA5LWU1MjQtNDZmMy04NjVhLTMyYTc0NGVhMGJlNSIsImlhdCI6MTc2ODMwNDQ2Nywic3ViIjoiZGV2ZWxvcGVyLzgxM2FkZGQyLTJjYTgtMjY0Yy1mMTM3LWQ4MmMxY2EzYzgxYiIsInNjb3BlcyI6WyJyb3lhbGUiXSwibGltaXRzIjpbeyJ0aWVyIjoiZGV2ZWxvcGVyL3NpbHZlciIsInR5cGUiOiJ0aHJvdHRsaW5nIn0seyJjaWRycyI6WyIxODUuNTUuMzguMTkwIl0sInR5cGUiOiJjbGllbnQifV19.5qva6HAJpCKQS68naADyJS5M08dprrZ_0qLAMWm_rdEyqpZrY0-WLW3B-y6d_6xMXlZoBCQjwFcORhxwVofS7A"

BASE_URL = "https://api.clashroyale.com/v1"

@app.route('/', methods=['POST'])
def proxy():
    data = request.json
    player_tag = data.get('playerTag', '').upper().replace('#', '')
    mode = data.get('mode', '')

    headers = {"Authorization": f"Bearer {CR_API_KEY}"}

    try:
        if mode == 'battlelog':
            # Fetch Battle Log
            url = f"{BASE_URL}/players/%23{player_tag}/battlelog"
            response = requests.get(url, headers=headers)
            return jsonify(response.json())
        
        else:
            # Fetch Player Profile
            url = f"{BASE_URL}/players/%23{player_tag}"
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                return jsonify({"error": "Player not found"}), 404

            d = response.json()
            
            # Format data for the HTML frontend
            stats = {
                "tag": f"#{player_tag}",
                "name": d.get("name"),
                "trophies": d.get("trophies"),
                "bestRank": d.get("bestPathOfLegendsSeasonResult", {}).get("rank") or 
                            d.get("leagueStatistics", {}).get("bestSeason", {}).get("rank") or 0,
                "avatarUrl": f"https://ui-avatars.com/api/?name={d.get('name')}&background=random",
                "favoriteCard": d.get("currentFavouriteCard", {}).get("name", "Unknown")
            }
            return jsonify(stats)

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("⚔️  Clash Royale API Proxy running on port 8000...")
    app.run(port=8000)