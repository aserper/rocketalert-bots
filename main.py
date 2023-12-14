import json
import os
import threading
import math
import requests
from mastodon import Mastodon
from datetime import date
import schedule
from time import sleep

print("Program started")
masto_user = os.environ['MASTO_USER']
masto_password = os.environ['MASTO_PASSWORD']
masto_clientid = os.environ['MASTO_CLIENTID']
masto_clientsecret = os.environ['MASTO_CLIENTSECRET']
masto_api_baseurl = os.environ['MASTO_BASEURL']

# Lock for synchronization
alerts_lock = threading.Lock()

# Function to fetch SSE events from the given URL
def fetch_sse_events(url):
    try:
        print("Opening SSE connection to fetch events")
        response = requests.get(url, stream=True)
        response.encoding = 'utf-8'

        for line in response.iter_lines(decode_unicode=True):
            line = line.lstrip("data:")
            print(f"Got event: {line}")

            if line.strip():  # Check if the line is not empty
                try:
                    event_data = json.loads(line)
                    yield event_data
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
    except Exception as ex:
        print(f"Error fetching SSE events: {ex}")

# List to store alerts
alerts = []

# Function to handle SSE events and append alerts
def handle_sse_events(sse_url):
    global alerts
    try:
        for event_data in fetch_sse_events(sse_url):
            area_name_en = event_data.get('areaNameEn', '')
            city_name_he = event_data.get('name', '')
            city_name_en = event_data.get('englishName', '')
            timestamp = event_data.get('timeStamp', '')

            alert_text = f"Town/city: {city_name_en}/{city_name_he}\n" \
                         f"District Name: {area_name_en}\n" \
                         f"Local time in Israel: {timestamp}\n\n"

            split_alerts = split_alert_text(alert_text)

            with alerts_lock:
                alerts.extend(split_alerts)

    except Exception as e:
        print(f"Error processing SSE events: {e}")

# Function to split text into multiple posts if it exceeds 500 characters
def split_alert_text(text):
    max_length = 500
    num_parts = math.ceil(len(text) / max_length)
    split_alerts = []

    for i in range(num_parts):
        start = i * max_length
        end = (i + 1) * max_length
        part_text = text[start:end]
        split_alerts.append(f"{part_text}")

    return split_alerts

# Function to post combined alerts to Mastodon
def post_combined_alerts(username, password):
    global alerts
    mastodon_instance = Mastodon(
        api_base_url=masto_api_baseurl,
        client_id=masto_clientid,
        client_secret=masto_clientsecret,
    )

    mastodon_instance.log_in(username=username, password=password, scopes=['read', 'write'])

    while True:
        if alerts:
            with alerts_lock:
                combined_message = "🚨🚀🚨 Rocket alerts in Israel 🚨🚀🚨\n\n" + "\n".join(alerts) + \
                                   "\nLearn more at https://rocketalert.live"
                max_length = 500
                message_parts = [combined_message[i:i + max_length] for i in range(0, len(combined_message), max_length)]

                for i, part in enumerate(message_parts):
                    mastodon_instance.toot(part)
                    print(f"Part {i + 1}/{len(message_parts)} posted successfully:\n{part}")

                alerts = []

        sleep(1)  # Sleep to reduce CPU usage

# Function to get daily total of alerts
def alert_daily_total(day=str(date.today())):
    url = f"https://ra-agg.kipodopik.com/api/v1/alerts/total?from={day}&to={day}"
    response = requests.get(url).json()
    print("Fetching daily total")
    if response["success"]:
        print("Daily total fetched")
        return response["payload"]
    else:
        print(f"Something went wrong, Error:{response['error']}")
        print("Please note the function only takes dates in string format (YYYY-MM-DD)")

# Function to post daily summary of alerts to Mastodon
def post_daily_summary(username, password):
    print(f"Attempting to post daily total to {username}")
    mastodon_instance = Mastodon(
        api_base_url=masto_api_baseurl,
        client_id=masto_clientid,
        client_secret=masto_clientsecret,
    )

    mastodon_instance.log_in(username=username, password=password, scopes=['read', 'write'])

    daily_total = alert_daily_total()
    daily_message = f"📢 Daily Summary, {date.today()}: 📢\n\nTotal number of rockets fired into Israel: {daily_total}" \
                    f"\n\nLearn more at https://rocketalert.live"

    mastodon_instance.toot(daily_message)
    print(f"Daily total posted to {username}")

# Main script
if __name__ == "__main__":
    SSL_URL = "https://ra-agg.kipodopik.com/api/v1/alerts/real-time"

    sse_thread = threading.Thread(target=handle_sse_events, args=(SSL_URL,))
    sse_thread.daemon = True
    sse_thread.start()

    post_thread = threading.Thread(target=post_combined_alerts, args=(masto_user, masto_password))
    post_thread.daemon = True
    post_thread.start()

    schedule.every().day.at("23:55").do(post_daily_summary, username=masto_user, password=masto_password)

    try:
        while True:
            schedule.run_pending()
            sleep(1)  # Sleep to reduce CPU usage
    except KeyboardInterrupt:
        print("Program terminated")