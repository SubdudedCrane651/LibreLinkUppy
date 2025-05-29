import requests
import hashlib
import json
import os
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime, timedelta
import time
import pygame

pygame.init()
#pygame.mixer.init()

LAST_ALARM_TIME = 0

class LibreLinkUpClient:
    def __init__(self):
        self.auth_token = None
        self.patient_id = None
        self.sha256_hash = None
        self.headers = {
            "Accept-Encoding": "gzip",
            "Pragma": "no-cache",
            "Connection": "Keep-Alive",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "Sec-CH-UA-Mobile": "?0",
            "User-Agent": "HTTP Debugger/9.0.0.12",
            "Product": "llu.android",
            "Version": "4.12.0",
            "Cache-Control": "no-cache"
        }
        self.glucose_data = []  

    def load_credentials(self):
        """Load email and password from JSON file"""
        json_file_path = os.path.join(os.path.expanduser("~"), "Documents", "credentials.json")

        if not os.path.exists(json_file_path):
            return None

        with open(json_file_path, "r") as file:
            return json.load(file)

    def login(self):
        credentials = self.load_credentials()

        if not credentials or "email" not in credentials or "password" not in credentials:
            print("⚠ No credentials found. Please enter your email and password.")
            self.prompt_user()
            credentials = self.load_credentials()

        email = credentials["email"]
        password = credentials["password"]

        login_url = "https://api.libreview.io/llu/auth/login"
        con_url = "https://api.libreview.io/llu/connections"

        request_body = {"email": email, "password": password}
        response = requests.post(login_url, json=request_body, headers=self.headers)
        
        json_response = response.json()
        error_code = json_response.get("status")

        #Email or password incorrect try again
        if error_code == 2:
            os.system("cls")
            print("⚠ Invalid email or password. Please re-enter.")
            self.prompt_user()
            return False

        if response.status_code == 200:
            json_login = response.json()
            region = json_login["data"].get("region")

            if region:
                login_url = f"https://api-{region}.libreview.io/llu/auth/login"
                con_url = f"https://api-{region}.libreview.io/llu/connections"
                response = requests.post(login_url, json=request_body, headers=self.headers)
                if response.status_code != 200:
                    return False
                json_login = response.json()

            self.auth_token = json_login["data"]["authTicket"]["token"]
            self.patient_id = json_login["data"]["user"]["id"]
            self.sha256_hash = self.compute_sha256_hash(self.patient_id)

            self.headers["Authorization"] = f"Bearer {self.auth_token}"
            self.headers["Account-Id"] = self.sha256_hash

            response = requests.get(con_url, headers=self.headers)
            if response.status_code == 200:
                json_con = response.json()
                self.patient_id = json_con["data"][0]["patientId"]
                
                # ✅ Save valid credentials back to JSON file
                self.save_credentials(email, password)
                return True
        
        # print("⚠ Invalid email or password. Please re-enter.")
        # self.prompt_user()
        # return False

    def save_credentials(self, email, password):
        """Save valid credentials to the JSON file"""
        json_file_path = os.path.join(os.path.expanduser("~"), "Documents", "credentials.json")
        credentials = {"email": email, "password": password}

        with open(json_file_path, "w") as file:
            json.dump(credentials, file, indent=4)

    def prompt_user(self):
        """Prompt user for credentials and save to JSON"""
        email = input("Enter your email: ")
        password = input("Enter your password: ")

        self.save_credentials(email, password)

    def get_glucose_data(self):
        global LAST_ALARM_TIME

        if not self.auth_token or not self.patient_id:
            raise ValueError("Not authenticated. Call login() first.")

        glucose_url = f"https://api.libreview.io/llu/connections/{self.patient_id}/graph"
        response = requests.get(glucose_url, headers=self.headers)

        if response.status_code == 200:
            return self.parse_graph_data(response.json())

        raise Exception(f"Failed to retrieve glucose data: {response.status_code}")

    def parse_graph_data(self, json_resp):
        """Parse and store all glucose readings"""
        new_data = []

        if "graphData" in json_resp["data"]:
            for item in json_resp["data"]["graphData"]:
                new_data.append({
                    "timestamp": datetime.strptime(item["Timestamp"], "%m/%d/%Y %I:%M:%S %p"),
                    "value": float(item["Value"])
                })

        if "glucoseMeasurement" in json_resp["data"]["connection"]:
            data = json_resp["data"]["connection"]["glucoseMeasurement"]
            latest_entry = {
                "timestamp": datetime.strptime(data["Timestamp"], "%m/%d/%Y %I:%M:%S %p"),
                "value": float(data["Value"])
            }
            new_data.append(latest_entry)

        self.glucose_data = new_data

    @staticmethod
    def compute_sha256_hash(input_string):
        sha256_hash = hashlib.sha256()
        sha256_hash.update(input_string.encode("utf-8"))
        return sha256_hash.hexdigest()

# ✅ Run the client and fetch glucose data
client = LibreLinkUpClient()

while not client.login():
    pass
    # print("⚠ Invalid credentials, please try again...")

print("Login successful!") 

# ✅ Set up real-time line chart
fig, ax = plt.subplots()
times = []
values = []

def sound_alarm():
    #winsound.Beep(1000, 1000)  # ✅ Beeps for 1 second at 1000 Hz
    pygame.mixer.music.load("telephone-ring.mp3")  # ✅ Ensure `alarm.mp3` is in your working directory
    pygame.mixer.music.play()

    
import pyttsx3

engine = pyttsx3.init()

def speak_hypo_alert():
    engine.say("You are presently in Hypo. Please take action.")
    engine.runAndWait()

def update_graph(i):
    global LAST_ALARM_TIME

    """Fetch new glucose data and update the chart."""
    client.get_glucose_data()  # Fetch latest data every 5 sec

    if client.glucose_data:
        times = [entry["timestamp"] for entry in client.glucose_data]  # ✅ Keep timestamps as datetime objects
        values = [entry["value"] for entry in client.glucose_data]

        ax.clear()
        ax.plot(times, values, marker="o", linestyle="-", color="b")

        # ✅ Display the last glucose reading with DATE & TIME
        last_entry = client.glucose_data[-1]
        ax.text(times[-1], values[-1], f"{last_entry['timestamp'].strftime('%m/%d/%Y %H:%M:%S')}\n{last_entry['value']} mmol/L", 
                fontsize=12, color="red", ha="right")
        
        if last_entry['value'] < 4:
            current_time = time.time()
            if current_time - LAST_ALARM_TIME >= 60:  # ✅ Ensure alarm triggers only once per minute
                sound_alarm()
                speak_hypo_alert()
                LAST_ALARM_TIME = current_time  # ✅ Update last alarm time

        ax.set_xlabel("Time (HH:00)")
        ax.set_ylabel("Glucose Level (mmol/L)")
        ax.set_title("Real-time Glucose Monitoring")

        # ✅ Set x-axis ticks at 1-hour intervals (HH:00 format)
        first_time = times[0].replace(minute=0, second=0)  # Start at the first full hour
        last_time = times[-1]
        hourly_ticks = [first_time + timedelta(hours=i) for i in range((last_time - first_time).seconds // 3600 + 1)]
        
        ax.set_xticks(hourly_ticks)
        ax.set_xticklabels([t.strftime("%H:00") for t in hourly_ticks], rotation=45, ha="right")

        plt.grid()

# ✅ Auto-refresh chart every 5 seconds
ani = animation.FuncAnimation(fig, update_graph, interval=5000)

plt.show()