import json
import os
import requests

WEBHOOK_URL = "http://10.0.0.205:8123/api/webhook/salon_speak"

def trigger_google_home_mini():
        url = WEBHOOK_URL
        try:
            requests.post(url)
            print("Google Home Mini alert triggered")
        except Exception as e:
            print("Error triggering Google Home Mini:", e)

IFTTT_file_path = os.path.join("IFTTT", "KEY.json")
#print(f"Loading credentials from: {IFTTT_file_path}")
        
with open(IFTTT_file_path, "r") as file:
     IFTTT_config = json.load(file)        

IFTTT_KEY = IFTTT_config[0]
EVENT = "low_glucose"

def trigger_alexa():
        url = f"https://maker.ifttt.com/trigger/{EVENT}/with/key/{IFTTT_KEY}"
        try:
            requests.post(url)
            print("Alexa alert triggered")
        except Exception as e:
            print("Error triggering Alexa:", e)             

if __name__ == "__main__":    trigger_google_home_mini()    