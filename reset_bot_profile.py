import sys
import requests

def reset_profile(token):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    base_url = f"https://api.telegram.org/bot{token}"

    print("Restoring bot name...")
    r1 = requests.post(f"{base_url}/setMyName", json={"name": "Auto Mail Bot"})
    print("setMyName:", r1.json())

    print("Restoring bot description...")
    r2 = requests.post(f"{base_url}/setMyDescription", json={"description": "Automated Outreach Telegram Bot for Lead Processing and Campaign Execution."})
    print("setMyDescription:", r2.json())

    print("Restoring bot short description...")
    r3 = requests.post(f"{base_url}/setMyShortDescription", json={"short_description": "Auto Mail Outreach Telegram Bot"})
    print("setMyShortDescription:", r3.json())

if __name__ == "__main__":
    token = sys.argv[1] if len(sys.argv) > 1 else "8460543006:AAGKnlnbTPSkg7vGntQISVuL5vomjiNeiBk"
    reset_profile(token)
