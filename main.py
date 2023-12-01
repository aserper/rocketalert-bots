from mastodon import Mastodon
import json, requests
from datetime import datetime

today_date = datetime.now().date()
formatted_date = today_date.strftime("%Y-%m-%d")

# Register your app! This only needs to be done once (per server, or when
# distributing rather than hosting an application, most likely per device and server).
# Uncomment the code and substitute in your information:

Mastodon.create_app(
    'rocketalert',
    api_base_url = 'https://mastodon.social',
    to_file = 'pytooter_clientcred.secret'
)


# Then, log in. This can be done every time your application starts (e.g. when writing a
# simple bot), or you can use the persisted information:
mastodon = Mastodon(client_id = 'pytooter_clientcred.secret',)
mastodon.log_in(
    'aserper+rocketalert@gmail.com',
    '!)5oMS@MFJp$vOw4+NAK',
    to_file = 'pytooter_usercred.secret'
)
json_data = requests.get("https://ra-agg.kipodopik.com/api/v1/alerts/daily?from={0}&to={0}".format(formatted_date)).content
data = json.loads(json_data)
payload = data["payload"]

# Note that this won't work when using 2FA - you'll have to use OAuth, in that case.
# To post, create an actual API instance:
mastodon = Mastodon(access_token = 'pytooter_usercred.secret')
mastodon.toot('Number of alerts in Israel today: {}. Learn more at https://rocketalert.live #IsraelUnderAttack #Israel #rockets'.format(str(payload[0]['alerts'])))
