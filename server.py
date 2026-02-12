import time
import requests
import firebase_admin
from firebase_admin import credentials, messaging
from flask import Flask, request, jsonify
from threading import Thread
from bs4 import BeautifulSoup
import os
import json

app = Flask(__name__)

# Firebase init from environment
cred = credentials.Certificate(
    json.loads(os.environ["FIREBASE_JSON"])
)
firebase_admin.initialize_app(cred)

tracking = False
device_token = None
train_number = None
travel_date = None
current_active = False


def send_notification(message):
    msg = messaging.Message(
        notification=messaging.Notification(
            title="Train Alert",
            body=message,
        ),
        token=device_token,
    )
    messaging.send(msg)


def get_train_status():
    try:
        url = f"https://erail.in/train-enquiry/{train_number}?date={travel_date}"
        r = requests.get(url, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text()

        if "CURRENT" in text:
            idx = text.find("CURRENT")
            return text[idx:idx+15]
        return None
    except:
        return None


def tracking_loop():
    global tracking, current_active

    while True:
        if tracking and device_token:
            status = get_train_status()
            print("Status:", status)

            if status:
                current_active = True
                send_notification(f"Current available seats - {status}")

            elif current_active:
                send_notification("No current availability. Tracking stopped.")
                tracking = False
                current_active = False

        time.sleep(600)


@app.route("/start", methods=["POST"])
def start_tracking():
    global tracking, device_token, train_number, travel_date, current_active

    data = request.json
    device_token = data["token"]
    train_number = data["train"]
    travel_date = data["date"]

    tracking = True
    current_active = False

    return jsonify({"message": "Tracking started"})


@app.route("/")
def home():
    return "Server running"


if __name__ == "__main__":
    Thread(target=tracking_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=3000)
