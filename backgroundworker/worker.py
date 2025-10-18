import time
import requests

RENDER_APP_URL = "https://locomoco.top"

while True:
    try:
        r = requests.get(RENDER_APP_URL)
        print(f"Pinged {RENDER_APP_URL}: {r.status_code}")
    except Exception as e:
        print(f"Error pinging: {e}")
    time.sleep(600)  # Wait 10 minutes