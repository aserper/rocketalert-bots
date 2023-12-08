import json
import os
import threading
import math
import requests
from mastodon import Mastodon
import queue

print("Program started")
masto_user = os.environ['MASTO_USER']
masto_password = os.environ['MASTO_PASSWORD']
masto_clientid = os.environ['MASTO_CLIENTID']
masto_clientsecret = os.environ['MASTO_CLIENTSECRET']

# Lock for synchronization
alerts_lock = threading.Lock()

# Create a thread-safe queue to buffer incoming events
event_queue = queue.Queue()

# Function to fetch SSE events from the given URL
def fetch_sse_events(url):
    try:
        print("Opening SSE connection to fetch events")
        response = requests.get(url, stream=True)
        response.encoding = 'utf-8'

        for line in response.iter_lines(decode_unicode=True):
            # Remove the "data:" prefix from each line
            line = line.lstrip("data:")
            print("Got event")

            if line.strip():  # Check if the line is not empty
                try:
                    event_data = json.loads(line)
                    yield event_data
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
    except Exception as ex:
        print(f"Error fetching SSE events: {ex}")

# Function to handle SSE events and append them to the queue
def handle_sse_events(sse_url):
    try:
        for event_data in fetch_sse_events(sse_url):
            area_name_en = event_data.get('areaNameEn', '')
            city_name_he = event_data.get('name', '')
            city_name_en = event_data.get('englishName', '')
            timestamp = event_data.get('timeStamp', '')

            # Create the alert text
            alert_text = f"Town/city: {city_name_en}/{city_name_he}\n" \
                         f"District Name: {area_name_en}\n" \
                         f"Timestamp: {timestamp}\n\n"

            # Split the alert text into multiple posts if it exceeds 500 characters
            split_alerts = split_alert_text(alert_text)

            with alerts_lock:
                # Append the split alerts to the queue
                event_queue.put(split_alerts)

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
        split_alerts.append(f"{part_text} (Part {i + 1}/{num_parts})")

    return split_alerts

# Function to process events from the queue and post them to Mastodon
def process_events_from_queue(username, password):
    global alerts
    mastodon_instance = Mastodon(
        api_base_url='https://mastodon.social',  # Replace with your Mastodon instance URL
        client_id=masto_clientid,  # Replace with your Mastodon client ID
        client_secret=masto_clientsecret,  # Replace with your Mastodon client secret
    )

    # Log in with username and password
    mastodon_instance.log_in(username=username, password=password, scopes=['read', 'write'])

    while True:
        try:
            # Get events from the queue
            alerts = event_queue.get()

            if alerts:
                # Create a combined message from all alerts
                combined_message = "🚨🚨🚨 Rocket alerts in Israel 🚨🚨🚨\n\n" + "\n".join(alerts) + \
                                "\nLearn more at https://rocketalert.live"

                # Split the combined message into parts no longer than 500 characters
                max_length = 500
                message_parts = [combined_message[i:i + max_length] \
                                for i in range(0, len(combined_message), max_length)]

                for i, part in enumerate(message_parts):
                    # Post each part as a separate toot
                    mastodon_instance.toot(part)
                    print(f"Part {i + 1}/{len(message_parts)} posted successfully:\n{part}")

                # Clear the alerts list
                alerts = []

        except Exception as e:
            print(f"Error processing events from the queue: {e}")

# Main script
if __name__ == "__main__":
    # URL for fetching SSE events
    SSL_URL = "https://ra-agg.kipodopik.com/api/v1/alerts/real-time"

    # Start a thread to handle SSE events and append events to the queue
    sse_thread = threading.Thread(target=handle_sse_events, args=(SSL_URL,))
    sse_thread.daemon = True
    sse_thread.start()

    # Start a thread to process events from the queue and post to Mastodon
    process_thread = threading.Thread(target=process_events_from_queue, args=(masto_user, masto_password))
    process_thread.daemon = True
    process_thread.start()

    # Keep the main thread running
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Program terminated")
