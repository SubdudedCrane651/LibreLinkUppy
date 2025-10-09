import requests
import hashlib
import json
import os
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime, timedelta
import time
import pygame
import mysql.connector

pygame.init()
#pygame.mixer.init()

LAST_ALARM_TIME = 0

class LibreLinkUpClient:
    def __init__(self):
        self.auth_token = None
        self.patient_id = None
        self.sha256_hash = None
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "LibreLinkUp/4.16.0 Android",
            "Accept": "application/json",
            "version": "4.16.0",
            "Accept-Encoding": "gzip",
            "Pragma": "no-cache",
            "Connection": "Keep-Alive",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "Sec-CH-UA-Mobile": "?0",
            "User-Agent": "HTTP Debugger/9.0.0.12",
            "Product": "llu.android",
            "Cache-Control": "no-cache"
        }
        self.glucose_data = []  
        
 
    #Json format for mysql_config.json in your documents folder
    #{  
    #       "host":"hostname",
    #       "user":"username",
    #       "password":"password123",
    #       "database":"databasename"
    #}
     
    def load_mysql_config(self):
        """Load MySQL config from separate JSON file"""
        json_file_path = os.path.join(os.path.expanduser("~"), "Documents", "mysql_config.json")

        if not os.path.exists(json_file_path):
            print("⚠ MySQL config file not found.")
            return None

        try:
            with open(json_file_path, "r") as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing MySQL config: {e}")
            return None

    def connect_to_mysql(self):
        config = self.load_mysql_config()
        if not config:
            return None

        try:
            connection = mysql.connector.connect(
                host=config["host"],
                user=config["user"],
                password=config["password"],
                database=config["database"],
                charset="utf8mb4",
                #cursorclass="pymysql.cursors.Cursor",
                connect_timeout=5
            )
            print("✅ Connected to MySQL")
            return connection
        except mysql.connector.Error as err:
            print(f"❌ MySQL connection error: {err}")
            return None

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
        
    def insert_graph_data(self, new_data):
        config = self.load_mysql_config()
        if not config:
            print("⚠ MySQL config missing or invalid.")
            return

        connection = self.connect_to_mysql()
        if not connection:
            print("⚠ Skipping insert: No valid MySQL connection.")
            return
        
        try:
            cursor = connection.cursor()
            
             # 🧹 Delete readings older than 8 hours
            cutoff = datetime.now() - timedelta(hours=8)
            delete_query = "DELETE FROM glucose_readings WHERE timestamp < %s"
            cursor.execute(delete_query, (cutoff,))
            print(f"🧹 Deleted readings older than {cutoff.strftime('%Y-%m-%d %H:%M:%S')}")

            for entry in new_data:
                # Check if timestamp already exists
                check_query = "SELECT COUNT(*) FROM glucose_readings WHERE timestamp = %s"
                cursor.execute(check_query, (entry["timestamp"],))
                count = cursor.fetchone()[0]

                if count > 0:
                    print(f"⚠ Skipping duplicate reading: {entry['timestamp']}")
                    continue

                try:
                    cursor = connection.cursor()
                    
                     # 🧹 Delete readings older than 8 hours
                    cutoff = datetime.now() - timedelta(hours=8)
                    delete_query = "DELETE FROM glucose_readings WHERE timestamp < %s"
                    cursor.execute(delete_query, (cutoff,))
                    print(f"🧹 Deleted readings older than {cutoff.strftime('%Y-%m-%d %H:%M:%S')}")


                    query = """
                        INSERT INTO glucose_readings (value, timestamp)
                        VALUES (%s, %s)
                    """
                    for entry in new_data:
                        cursor.execute(query, (entry["value"], entry["timestamp"]))
                    connection.commit()
                    print(f"✅ Inserted {len(new_data)} glucose readings.")
                except mysql.connector.Error as err:
                    print(f"❌ MySQL insert error: {err}")
                finally:
                    cursor.close()
                    connection.close()
                    
        except mysql.connector.Error as err:
                print(f"❌ MySQL error: {err}")         

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

        # ✅ Safely parse graphData
        graph_data = json_resp.get("data", {}).get("graphData", [])
        for item in graph_data:
            try:
                new_data.append({
                    "timestamp": datetime.strptime(item["Timestamp"], "%m/%d/%Y %I:%M:%S %p"),
                    "value": float(item["Value"])
                })
            except (KeyError, ValueError) as e:
                print(f"⚠ Skipping malformed graphData entry: {e}")
        
        # # ✅ Insert only the first (latest) reading
        # if new_data:
        #     latest = new_data[45]
        #     self.insert_graph_data([latest])  # Wrap in list to match expected input

        # ✅ Safely parse glucoseMeasurement from connection
        connection_data = json_resp.get("data", {}).get("connection", {})
        glucose_measurement = connection_data.get("glucoseMeasurement")

        if glucose_measurement:
            try:
                latest_entry = {
                    "timestamp": datetime.strptime(glucose_measurement["Timestamp"], "%m/%d/%Y %I:%M:%S %p"),
                    "value": float(glucose_measurement["Value"])
                }
                new_data.append(latest_entry)
            except (KeyError, ValueError) as e:
                print(f"⚠ Skipping malformed glucoseMeasurement entry: {e}")

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
    #winsound.Beep(1000, 1000)  # ✅ Beeps for 1 second at 1000 Hz8
    pygame.mixer.music.load("telephone-ring.mp3")  # ✅ Ensure `alarm.mp3` is in your working directory
    pygame.mixer.music.play()
    
import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty('voices')

for index, voice in enumerate(voices):
    print(f"{index}: {voice.name} - {voice.id}")

# Replace 0 with the index of the French voice you found

def speak_hypo_alert():
    #French voice using text2speech.py
    os.system('F:/Python/LibreLinkUppy/.venv/Scripts/python.exe text2speech.py "--lang=fr" "Vous êtes actuellement en hypoglycémie. Veuillez prendre des mesures."')
    #engine.say("You are presently in Hypo. Please take action.")
    #engine.runAndWait()

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
        
        client.insert_graph_data([last_entry])  # Wrap in list to match expected input
        
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

# ✅ Auto-refresh chart every 5 seconds 5000 1 minute 60000
ani = animation.FuncAnimation(fig, update_graph, interval=5000, cache_frame_data=False)

plt.show()