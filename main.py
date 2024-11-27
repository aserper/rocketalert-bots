import requests
import json
import signal
import sys
import faulthandler
from rocket_alert_api import RocketAlertAPI
from message_manager import MessageManager

def dump_traceback(sig, frame):
    print("\nReceived signal to dump traceback")
    faulthandler.dump_traceback()

def main():
    faulthandler.enable()
    signal.signal(signal.SIGUSR1, dump_traceback)

    messageManager = MessageManager()
    print("Connecting to server and starting listening to events...")

    while True:
        try:
            with RocketAlertAPI().listenToServerEvents() as response:
                response.encoding = "utf-8"
                for line in response.iter_lines(decode_unicode=True):
                    line = line.lstrip("data:")
                    # Check if the line is not empty
                    if line.strip():
                        print(f"Received server event: {line}")
                        eventData = json.loads(line)
                        alerts = eventData["alerts"]
                        # Keepalive check to please CF
                        if "KEEP_ALIVE" in alerts[0].get("name", ""):
                            print("DEBUG: Received Keep alive")
                        elif eventData is None:
                            print("Event is None.")
                        else:
                            print("Processing event...")
                            messageManager.postMessage(eventData)
                            print("Event process completed.")
                            print("")
        
        except KeyboardInterrupt:
            print("Program terminated")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
        except requests.exceptions.ChunkedEncodingError as err:
            print(f"Encountered 'InvalidChunkLength' error: {str(err)}")
            continue
        except Exception as e:
            print(f"Error main(): {e}")

if __name__ == "__main__":
    main()