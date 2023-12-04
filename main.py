import requests
import json
import threading
import math
from mastodon import Mastodon


# Function to fetch SSE events from the given URL
def fetch_sse_events(url):
    try:
        response = requests.get(url, stream=True)

        for line in response.iter_lines(decode_unicode=True):
            # Remove the "data:" prefix from each line
            line = line.lstrip("data:")

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

            # Create the alert text
            alert_text = f"Town/city: {city_name_en}/{city_name_he}\n" \
                         f"District Name: {area_name_en}\n" \
                         f"Timestamp: {timestamp}\n\n"

            # Split the alert text into multiple posts if it exceeds 500 characters
            split_alerts = split_alert_text(alert_text)

            # Append the split alerts to the list
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
        split_alerts.append(f"{part_text} (Part {i + 1}/{num_parts})")

    return split_alerts


# Function to post combined alerts to Mastodon
def post_combined_alerts(mastodon_instance):
    global alerts
    while True:
        if alerts:
            # Create a combined message from all alerts
            combined_message = "🚨🚨🚨 Rocket alerts in Israel 🚨🚨🚨\n\n" + "\n".join(alerts) + \
                               "\nLearn more at https://rocketalert.live"

            # Split the combined message into parts no longer than 500 characters
            max_length = 500
            message_parts = [combined_message[i:i + max_length] for i in range(0, len(combined_message), max_length)]

            for i, part in enumerate(message_parts):
                # Post each part as a separate toot
                mastodon_instance.toot(part)
                print(f"Part {i + 1}/{len(message_parts)} posted successfully:\n{part}")

            # Clear the alerts list
            alerts = []


# Main script
if __name__ == "__main__":
    # URL for fetching SSE events
    sse_url = "https://ra-agg.kipodopik.com/api/v1/alerts/real-time"

    # Use the persisted Mastodon information to log in
    mastodon_user = Mastodon(access_token='pytooter_usercred.secret')

    # Start a thread to handle SSE events and append alerts
    sse_thread = threading.Thread(target=handle_sse_events, args=(sse_url,))
    sse_thread.daemon = True
    sse_thread.start()

    # Start a thread to post combined alerts to Mastodon
    post_thread = threading.Thread(target=post_combined_alerts, args=(mastodon_user,))
    post_thread.daemon = True
    post_thread.start()

    # Keep the main thread running
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Program terminated")
