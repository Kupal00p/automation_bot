import threading
import time
import requests

def ping_self():
    while True:
        try:
            # ⚠️ Replace this with your Render URL later after deployment
            requests.get("https://automation-bot-5bho.onrender.com")
            print("Pinged site to keep it alive.")
        except Exception as e:
            print("Ping failed:", e)
        time.sleep(300)  # every 5 minutes

def keep_alive():
    thread = threading.Thread(target=ping_self)
    thread.daemon = True
    thread.start()
