#Clash Royale Tournament Manager

A web-based tool designed to organize, manage, and display Clash Royale tournaments easily. This project provides a public-facing dashboard for players to view standings and a secured admin panel for organizers to update scores in real-time.

## Features

* **Public Dashboard (`index.html`):** A clean interface for players and spectators to view the current tournament bracket, match schedules, and leaderboards.
* **Admin Panel (`zimperator.html`):** A restricted control panel where tournament organizers can:
    * Add or remove players.
    * Update match scores.
    * Advance winners to the next round.
* **Responsive Design:** Works on desktop and mobile for easy access during tournaments.

## 🛠️ Tech Stack

* **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
* **Hosting:** Compatible with GitHub Pages, Vercel, or any static hosting.
* **No Database Required:** Uses local storage or simple JSON handling (depending on specific implementation) for lightweight usage.

## 💻 How to Run Locally

Since this is a static project, you don't need `npm` or complicated installations. You just need a simple local server.

### Option 1: Using Python (Recommended)
If you have Python installed (Mac/Linux/Windows):

1.  Clone the repository:
    ```bash
    git clone [https://github.com/ayalgasimli/cr-tournament.git](https://github.com/ayalgasimli/cr-tournament.git)
    cd cr-tournament
    ```
2.  Start a simple HTTP server:
    ```bash
    python3 -m http.server
    ```
3.  Open your browser to the URL shown (usually `http://localhost:8000`).

### Option 2: Using VS Code Live Server
1.  Open the project folder in **VS Code**.
2.  Install the **"Live Server"** extension.
3.  Right-click `index.html` and select **"Open with Live Server"**.

## ☁️ How to Run in GitHub Codespaces

1.  Go to the repository page.
2.  Click **Code** > **Codespaces** > **Create codespace on main**.
3.  In the terminal, run:
    ```bash
    python3 -m http.server
    ```
4.  Click **"Open in Browser"** when the popup appears.
    * **Public View:** `...app.github.dev/index.html`
    * **Admin View:** `...app.github.dev/admin.html` (Append `/admin.html` to the URL manually).

## 📸 Screenshots

*(You can add screenshots of your tournament bracket here later)*

## 👤 Author

**Ayal Gasimli**
* GitHub: [@ayalgasimli](https://github.com/ayalgasimli)
* Student at Bilkent University (CTIS)

---
*Created for the love of Clash Royale.*(this is readme content is AI genareted, but works ig so idc)
