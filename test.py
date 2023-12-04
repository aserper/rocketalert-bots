import json
import threading
from mastodon import Mastodon

# Load test JSON data from a file
with open('test_alerts.json', 'r', encoding='utf-8') as json_file:
    test_data = json.load(json_file)

# Function to handle SSE events and generate alerts using test data
def generate_alerts():
    try:
        alerts = []
        for data in test_data:
            area_name_en = data.get('areaNameEn', '')
            city_name_he = data.get('name', '')
            city_name_en = data.get('englishName', '')
            timestamp = data.get('timeStamp', '')

            # Create the alert text
            alert_text = f"🚨🚨🚨 Rocket alerts in Israel 🚨🚨🚨\n" \
                         f"Town/city: {city_name_en}/{city_name_he}\n" \
                         f"District Name: {area_name_en}\n" \
                         f"Timestamp: {timestamp}\n\n"

            alerts.append(alert_text)

        return alerts
    except Exception as e:
        print(f"Error processing test data: {e}")
        return []

# Function to split text into multiple posts if it exceeds 500 characters combined
def split_alerts(alerts):
    max_length = 500
    split_alerts = []
    combined_alert = ""

    for alert in alerts:
        if len(combined_alert) + len(alert) <= max_length:
            combined_alert += alert
        else:
            split_alerts.append(combined_alert)
            combined_alert = alert

    if combined_alert:
        split_alerts.append(combined_alert)

    return split_alerts

# Function to post alerts to Mastodon
def post_alerts(mastodon_instance, alerts):
    for alert in alerts:
        if alert.strip():
            # Post the alert as a toot
            mastodon_instance.toot(alert)
            print(f"Alert posted successfully:\n{alert}")

# Main script
if __name__ == "__main__":
    # Use the persisted Mastodon information to log in
    mastodon_user = Mastodon(access_token='pytooter_usercred.secret')

    while True:
        # Generate alerts from test data
        alerts = generate_alerts()

        if alerts:
            # Split alerts if their combined length exceeds 500 characters
            split_alert_list = split_alerts(alerts)

            # Post alerts to Mastodon
            post_alerts(mastodon_user, split_alert_list)

    # Keep the main thread running
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Program terminated")
