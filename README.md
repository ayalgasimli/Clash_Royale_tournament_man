# Clash Royale Tournament Manager

A web-based tool designed to organize, manage, and display Clash Royale tournaments easily. This project provides a public-facing dashboard for players to view standings and a secured admin panel for organizers to update scores in real-time.

## Features

* **Public Dashboard (`index.html`):** A clean interface for players and spectators to view the current tournament bracket, match schedules, and leaderboards.
* **Admin Panel (`zimperator.html`):** A PIN-protected control panel where tournament organizers can:
    * Add or remove players.
    * Update match scores.
    * Auto-check battle results from the CR API.
    * Configure API server URL for deployment.
* **Responsive Design:** Works on desktop and mobile for easy access during tournaments.

## 🛠️ Tech Stack

* **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
* **Backend:** Python Flask API proxy for Clash Royale API
* **Database:** Supabase (PostgreSQL)
* **Hosting:** Compatible with GitHub Pages (frontend), any Python host for API.

## 💻 Setup Instructions

### 1. Get a Clash Royale API Key

1. Go to [developer.clashroyale.com](https://developer.clashroyale.com)
2. Create an account and generate an API key
3. **Important:** Whitelist your current IP address when generating the key

### 2. Set Up Environment Variables

Copy the example file and add your API key:

```bash
# Windows (Command Prompt)
set CR_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:CR_API_KEY="your_api_key_here"

# Linux/Mac
export CR_API_KEY=your_api_key_here
```

### 3. Run the API Server

```bash
pip install flask flask-cors requests python-dotenv
python api.py
```

### 4. Serve the Frontend

Using Python:
```bash
python -m http.server 3000
```

Or use VS Code Live Server extension.

### 5. Access the Application

* **Public Dashboard:** `http://localhost:3000/index.html`
* **Admin Panel:** `http://localhost:3000/zimperator.html`
  * First visit: Set a PIN (minimum 4 digits)
  * Subsequent visits: Enter your PIN to access

## ⚙️ Admin Settings

Click the ⚙️ button in the bottom-right corner to:
* Change the API server URL (for deployment)
* Reset your admin PIN

## 📸 Screenshots

*(You can add screenshots of your tournament bracket here later)*

## 👤 Author

**Ayal Gasimli**
* GitHub: [@ayalgasimli](https://github.com/ayalgasimli)
* Student at Bilkent University (CTIS)

---
*Created for the love of Clash Royale.*

