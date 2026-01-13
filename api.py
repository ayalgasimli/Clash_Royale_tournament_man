from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
# YOUR KEY from the Screenshot (Confirmed Correct)
CR_API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjY5ODE1YTI3LWU3ZjgtNGE0Ny1hNDU5LTczYTQ0YjMwYzI0MyIsImlhdCI6MTc2ODMwODk5NCwic3ViIjoiZGV2ZWxvcGVyLzgxM2FkZGQyLTJjYTgtMjY0Yy1mMTM3LWQ4MmMxY2EzYzgxYiIsInNjb3BlcyI6WyJyb3lhbGUiXSwibGltaXRzIjpbeyJ0aWVyIjoiZGV2ZWxvcGVyL3NpbHZlciIsInR5cGUiOiJ0aHJvdHRsaW5nIn0seyJjaWRycyI6WyIxMDQuMjguMjI0LjE3MyJdLCJ0eXBlIjoiY2xpZW50In1dfQ.A0sYJPDn0iRcSRB2keXlJO3qHOB9cP6qgfpugjP56v7SyTfsNd2u3_FINXACzS58I8P5EzUkWsuq4RWX3qIFYQ"

BASE_URL = "https://api.clashroyale.com/v1"

@app.route('/', methods=['POST'])
def proxy():
    try:
        data = request.json
        # Clean the tag: remove # and spaces, ensure uppercase
        raw_tag = data.get('playerTag', '')
        player_tag = raw_tag.upper().replace('#', '').strip()
        mode = data.get('mode', '')

        print(f"🔹 Requesting Tag: {player_tag} | Mode: {mode}")

        headers = {
            "Authorization": f"Bearer {CR_API_KEY}",
            "Accept": "application/json"
        }

        if mode == 'battlelog':
            url = f"{BASE_URL}/players/%23{player_tag}/battlelog"
        else:
            url = f"{BASE_URL}/players/%23{player_tag}"

        # Send request to Clash Royale
        response = requests.get(url, headers=headers)
        
        # ERROR HANDLING
        if response.status_code != 200:
            print(f"❌ CR API Error {response.status_code}: {response.text}")
            return jsonify(response.json()), response.status_code

        d = response.json()
        
        if mode == 'battlelog':
             return jsonify(d)
        
        # Format Profile Data
        stats = {
            "tag": f"#{player_tag}",
            "name": d.get("name"),
            "trophies": d.get("trophies"),
            "bestRank": d.get("bestPathOfLegendsSeasonResult", {}).get("rank") or 
                        d.get("leagueStatistics", {}).get("bestSeason", {}).get("rank") or 0,
            "avatarUrl": f"https://ui-avatars.com/api/?name={d.get('name')}&background=random",
            "favoriteCard": d.get("currentFavouriteCard", {}).get("name", "Unknown")
        }
        print("✅ Success!")
        return jsonify(stats)

    except Exception as e:
        print(f"🔥 Python Server Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("⚔️  Clash Royale API Proxy running on port 8000...")
    # host='0.0.0.0' fixes some local connection issues
    app.run(host='0.0.0.0', port=8000)