from mastodon import Mastodon
import json
from sseclient import SSEClient
from datetime import datetime
import threading

today_date = datetime.now().date()
formatted_date = today_date.strftime("%Y-%m-%d")

# Register your app! This only needs to be done once (per server, or when
# distributing rather than hosting an application, most likely per device and server).
# Uncomment the code and substitute in your information:
print("Program started")
Mastodon.create_app(
    'rocketalert',
    api_base_url='https://mastodon.social',
    to_file='pytooter_clientcred.secret'
)
print("Mastodon connection object created")
# Then, log in. This can be done every time your application starts (e.g., when writing a
# simple bot), or you can use the persisted information:
mastodon = Mastodon(client_id='pytooter_clientcred.secret',)
mastodon.log_in(
    'aserper+rocketalert@gmail.com',
    '!)5oMS@MFJp$vOw4+NAK',
    to_file='pytooter_usercred.secret'
)
print("Logged in")

# List to store alerts
alerts = []

# Function to handle SSE events and append alerts
def handle_sse_events():
    sse_url = "https://ra-agg.kipodopik.com/api/v1/alerts/real-time"  # Replace with your SSE stream URL
    client = SSEClient(sse_url)  # Create the SSEClient object
    try:
        for event in client:
            if event.event == 'message':
                try:
                    if event.data:
                        data = json.loads(event.data)
                        area_name_en = data.get('areaNameEn', '')
                        city_name_he = data.get('name', '')
                        city_name_en = data.get('englishName', '')
                        timestamp = data.get('timeStamp', '')

                        # Create the alert text
                        alert_text = f"Town/city: {city_name_en}/{city_name_he}\n" \
                                     f"District Name: {area_name_en}\n" \
                                     f"Timestamp: {timestamp}\n\n"

                        # Append the alert to the list
                        alerts.append(alert_text)
                except Exception as e:
                    print(f"Error processing SSE event: {e}")
    finally:
        client.close()  # Close the SSEClient when done

# Function to post combined alerts to Mastodon
def post_combined_alerts(mastodon_instance):
    global alerts
    while True:
        if alerts:
            # Create a combined message from all alerts
            combined_message = "🚨🚨🚨 Rocket alerts in Israel 🚨🚨🚨\n\n" + "\n".join(alerts) + \
                              "Learn more at https://rocketalert.live"

            # Post the combined message to Mastodon
            mastodon_instance.toot(combined_message)

            # Log to stdout that the message was posted successfully
            print("Message posted successfully:\n{0}".format(combined_message))

            # Clear the alerts list
            alerts = []

# Main script
if __name__ == "__main__":
    # Use the persisted Mastodon information to log in
    mastodon_user = Mastodon(access_token='pytooter_usercred.secret')

    # Start a thread to handle SSE events and append alerts
    sse_thread = threading.Thread(target=handle_sse_events)
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
