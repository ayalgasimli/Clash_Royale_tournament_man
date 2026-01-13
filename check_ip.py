import requests
import time

try:
    print("--- CHECKING YOUR REAL IP ---")
    ip = requests.get('https://api64.ipify.org').text
    print(f"Your IP is: {ip}")
    print("-----------------------------")
except Exception as e:
    print(f"Error: {e}")

# This line forces the window to stay open
input("\nPress ENTER to close this window...")