import requests
import sys

# --- PASTE YOUR LONG KEY HERE ---
KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImEwM2QyMmI3LWZkNjctNGQ2MS04NjkzLWNlZjk3YmE4NjcwMyIsImlhdCI6MTc2ODMwODMzMywic3ViIjoiZGV2ZWxvcGVyLzgxM2FkZGQyLTJjYTgtMjY0Yy1mMTM3LWQ4MmMxY2EzYzgxYiIsInNjb3BlcyI6WyJyb3lhbGUiXSwibGltaXRzIjpbeyJ0aWVyIjoiZGV2ZWxvcGVyL3NpbHZlciIsInR5cGUiOiJ0aHJvdHRsaW5nIn0seyJjaWRycyI6WyIxODUuNTUuMzkuNTIiLCIxODUuNTUuMzkuMTMiXSwidHlwZSI6ImNsaWVudCJ9XX0.kWOsgO6hx2Gwy2WCLHIFN3lDKsyqDirNwiV9IwsDLexitSyfI-mLrll3wqb_sui6j2WTyEFegsT7byCsw45MRA"
# --------------------------------

def test():
    print("\n--- 1. CHECKING IP ---")
    try:
        ip = requests.get('https://api64.ipify.org').text
        print(f"Python is sending requests from: {ip}")
    except:
        print("Could not check IP.")

    print("\n--- 2. TESTING CLASH ROYALE API ---")
    headers = {
        "Authorization": f"Bearer {KEY.strip()}", # .strip() removes accidental spaces
        "Accept": "application/json"
    }
    
    # We test with a known top player tag to be safe
    url = "https://api.clashroyale.com/v1/players/%232CCCP"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("✅ SUCCESS! The Key works perfectly.")
        print(f"Found Player: {response.json().get('name')}")
    else:
        print(f"❌ FAILED with Error {response.status_code}")
        print("REASON FROM SUPERCELL:")
        print(response.text)

    input("\nPress ENTER to close...")

if __name__ == "__main__":
    test()