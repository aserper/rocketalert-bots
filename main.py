from mastodon import Mastodon
import json
from sseclient import SSEClient
from datetime import datetime

today_date = datetime.now().date()
formatted_date = today_date.strftime("%Y-%m-%d")

# Register your app! This only needs to be done once (per server, or when
# distributing rather than hosting an application, most likely per device and server).
# Uncomment the code and substitute in your information:

Mastodon.create_app(
    'rocketalert',
    api_base_url='https://mastodon.social',
    to_file='pytooter_clientcred.secret'
)

# Then, log in. This can be done every time your application starts (e.g., when writing a
# simple bot), or you can use the persisted information:
mastodon = Mastodon(client_id='pytooter_clientcred.secret',)
mastodon.log_in(
    'aserper+rocketalert@gmail.com',
    '!)5oMS@MFJp$vOw4+NAK',
    to_file='pytooter_usercred.secret'
)

# Define a function to handle SSE events and post to Mastodon
def handle_sse_events(mastodon_instance):
    sse_url = "https://ra-agg.kipodopik.com/api/v1/alerts/real-time-test"  # Replace with your SSE stream URL
    client = SSEClient(sse_url)  # Create the SSEClient object
    try:
        for event in client:
            if event.event == 'message':
                try:
                    if event.data:
                        data = json.loads(event.data)
                        area_name_en = data.get('areaNameEn', '')
                        timestamp = data.get('timeStamp', '')

                        # Create the message text
                        message_text = f"🚨🚨🚨 Rocket alert in Israel 🚨🚨🚨\n Area Name: {area_name_en}\nTimestamp: " \
                                       f"{timestamp}\n Learn more at https://rocketalert.live"

                        # Post the message to Mastodon
                        mastodon_instance.toot(message_text)
                        #Log to stdout that the message was posted
                        print("Message posted sucsessfully: {0}".format(message_text))
                except Exception as e:
                    print(f"Error processing SSE event: {e}")
    finally:
        client.close()  # Close the SSEClient when done

# Main script
if __name__ == "__main__":
    # Use the persisted Mastodon information to log in
    mastodon_user = Mastodon(access_token='pytooter_usercred.secret')

    # Start listening to SSE events and posting to Mastodon
    handle_sse_events(mastodon_user)
