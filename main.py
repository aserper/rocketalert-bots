import requests
import json
import os
import signal
import sys
import faulthandler
from datetime import datetime
from rocket_alert_api import RocketAlertAPI
from message_manager import MessageManager

##TODO: Use a normal logging library. This is total שכונה

def dump_traceback(sig, frame):
    print(f"{datetime.now()} - Received signal to dump traceback")
    faulthandler.dump_traceback()


def main():
    faulthandler.enable()
    signal.signal(signal.SIGUSR1, dump_traceback)

    commit_sha = os.getenv("COMMIT_SHA", "unknown")
    print(f"{datetime.now()} - Starting version: {commit_sha}")
    print(f"{datetime.now()} - Connecting to server and starting to listen for events...")
    messageManager = MessageManager()

    while True:
        try:
            with RocketAlertAPI().listenToServerEvents() as response:
                response.encoding = "utf-8"
                for line in response.iter_lines(decode_unicode=True):
                    line = line.lstrip("data:")
                    if line.strip():
                        print(f"{datetime.now()} - Received server event: {line}")
                        eventData = json.loads(line)
                        alerts = eventData["alerts"]
                        if "KEEP_ALIVE" in alerts[0].get("name", ""):
                            print(f"{datetime.now()} - DEBUG: Received Keep alive")
                        elif eventData is None:
                            print(f"{datetime.now()} - Event is None.")
                        else:
                            print(f"{datetime.now()} - Processing event...")
                            messageManager.postMessage(eventData)
                            print(f"{datetime.now()} - Event process completed.\n")

        except KeyboardInterrupt:
            print(f"{datetime.now()} - Program terminated")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"{datetime.now()} - Error decoding JSON: {e}")
        except requests.exceptions.ChunkedEncodingError as err:
            print(f"{datetime.now()} - Encountered 'InvalidChunkLength' error: {str(err)}")
            continue
        except Exception as e:
            print(f"{datetime.now()} - Error main(): {e}")


if __name__ == "__main__":
    main()
