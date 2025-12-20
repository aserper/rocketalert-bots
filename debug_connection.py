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
    # Redact token from kwargs print
    if 'headers' in kwargs:
        h = kwargs['headers'].copy()
        for k in h:
             if 'SECURITY' in k.upper() or 'SECRET' in k.upper() or 'TOKEN' in k.upper():
                  h[k] = "***REDACTED***"
        print(f"Kwargs (Redacted): {kwargs.keys()} with Headers: {h}")
    else:
        print(f"Kwargs: {kwargs}")

    try:
        response = requests.get(URL, **kwargs)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print("Success! (Received headers)")
        if not kwargs.get('stream'):
             print(f"Body Length: {len(response.text)}")
        response.close()
    except Exception as e:
        print(f"FAILED: {e}")

def main():
    print(f"Testing connectivity to {BASE_URL}")
    
    # 0. Whitespace Check
    print(f"\n--- ENV CHECK ---")
    print(f"CUSTOM_HEADER_KEY height: {len(CUSTOM_HEADER_KEY)}")
    print(f"CUSTOM_HEADER_VALUE length: {len(CUSTOM_HEADER_VALUE)}")
    if CUSTOM_HEADER_VALUE != CUSTOM_HEADER_VALUE.strip():
        print("WARNING: CUSTOM_HEADER_VALUE has leading/trailing whitespace!")
        print(f"Stripped Length: {len(CUSTOM_HEADER_VALUE.strip())}")

    # 1. Basic Test (No Headers, No Stream)
    test_connection("1. Basic Request (No Headers)", timeout=10)

    # 2. Minimal Headers (ONLY the secret token)
    minimal_headers = { CUSTOM_HEADER_KEY.strip(): CUSTOM_HEADER_VALUE.strip() }
    test_connection("2. Minimal Headers (Only Token, Stripped)", headers=minimal_headers, timeout=10)

    # 3. Legacy UA (Firefox) - No SSE headers
    legacy_headers = {
        CUSTOM_HEADER_KEY.strip(): CUSTOM_HEADER_VALUE.strip(),
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/81.0"
    }
    test_connection("3. Legacy UA (Firefox 81)", headers=legacy_headers, timeout=10)

    # 4. Modern headers (The ones I added)
    modern_headers = {
        CUSTOM_HEADER_KEY.strip(): CUSTOM_HEADER_VALUE.strip(),
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/event-stream",
        "Cache-Control": "no-cache"
    }
    test_connection("4. Modern Headers (Chrome 120 + SSE)", headers=modern_headers, timeout=10)

    # 5. Disable Compression
    no_gzip_headers = modern_headers.copy()
    no_gzip_headers["Accept-Encoding"] = "identity"
    test_connection("5. No Compression (Accept-Encoding: identity)", headers=no_gzip_headers, timeout=10)

    # 6. Stream Test (Full Simulation)
    test_connection("6. Full App Simulation (Stream=True)", headers=modern_headers, stream=True, timeout=(10, 35))

if __name__ == "__main__":
    main()
