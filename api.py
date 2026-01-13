from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import time

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
# Load API key from environment variable
CR_API_KEY = os.environ.get("CR_API_KEY")

if not CR_API_KEY:
    print("⚠️  WARNING: CR_API_KEY environment variable is not set!")
    print("   Set it with: set CR_API_KEY=your_api_key (Windows)")
    print("   Or: export CR_API_KEY=your_api_key (Linux/Mac)")

BASE_URL = "https://api.clashroyale.com/v1"

# Rate limiting: track last request time
last_request_time = 0
MIN_REQUEST_INTERVAL = 0.5  # seconds between requests

@app.route('/', methods=['POST'])
def proxy():
    global last_request_time
    
    # Check if API key is configured
    if not CR_API_KEY:
        return jsonify({"error": "Server misconfigured: CR_API_KEY not set"}), 500
    
    try:
        # Rate limiting
        elapsed = time.time() - last_request_time
        if elapsed < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - elapsed)
        
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
        last_request_time = time.time()
        
        # ERROR HANDLING
        if response.status_code == 403:
            print("❌ API Key rejected - check if IP is whitelisted")
            return jsonify({"error": "API key IP mismatch. Generate a new key for your current IP."}), 403
        
        if response.status_code == 429:
            print("❌ Rate limited by Clash Royale API")
            return jsonify({"error": "Rate limited. Please wait a moment."}), 429
            
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
    if CR_API_KEY:
        print("✅ API Key loaded from environment")
    else:
        print("❌ No API key - requests will fail!")
    # host='0.0.0.0' fixes some local connection issues
    app.run(host='0.0.0.0', port=8000)