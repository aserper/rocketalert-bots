import requests
import os
import sys

# Default URL from environment or hardcoded fallback for testing
BASE_URL = os.environ.get('RA_BASEURL', 'https://ra-agg.kipodopik.com/api/v2/alerts')
URL = f"{BASE_URL}/real-time"

CUSTOM_HEADER_KEY = os.environ.get('CUSTOM_HEADER_KEY', 'x-ra-agg-secret')
CUSTOM_HEADER_VALUE = os.environ.get('CUSTOM_HEADER_VALUE', 'dummy_val')

def test_connection(name, **kwargs):
    print(f"\n--- TEST: {name} ---")
    print(f"URL: {URL}")
    print(f"Kwargs: {kwargs}")
    try:
        response = requests.get(URL, **kwargs)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {response.headers}")
        print("Success!")
        response.close()
    except Exception as e:
        print(f"FAILED: {e}")

def main():
    print(f"Testing connectivity to {BASE_URL}")

    # 1. Basic Test (No Headers, No Stream)
    test_connection("1. Basic Request (No Headers)", timeout=10)

    # 2. With Headers (No Stream)
    headers = {
        CUSTOM_HEADER_KEY: CUSTOM_HEADER_VALUE,
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive"
    }
    test_connection("2. With Headers (No Stream)", headers=headers, timeout=10)

    # 3. With Stream (Simulating App)
    test_connection("3. With Stream (Timeout 10, 35)", headers=headers, stream=True, timeout=(10, 35))

    # 4. No SSL Verify (Rule out cert issues)
    test_connection("4. No SSL Verify", headers=headers, stream=True, timeout=(10, 35), verify=False)

if __name__ == "__main__":
    main()
