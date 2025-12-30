# RocketAlert Bots - API Reference

## Table of Contents

1. [Overview](#overview)
2. [Module Reference](#module-reference)
   - [main.py](#mainpy)
   - [rocket_alert_api.py](#rocket_alert_apipy)
   - [message_manager.py](#message_managerpy)
   - [message_builder.py](#message_builderpy)
   - [telegram_bot.py](#telegram_botpy)
   - [mastodon_bot.py](#mastodon_botpy)
3. [Configuration Reference](#configuration-reference)
4. [Environment Variables](#environment-variables)
5. [Data Structures](#data-structures)
6. [Constants](#constants)
7. [Error Codes](#error-codes)
8. [Usage Examples](#usage-examples)

---

## Overview

This document provides comprehensive API documentation for all modules in the RocketAlert Bots system. Each section includes:

- Class and function signatures
- Parameter descriptions and types
- Return values and types
- Usage examples
- Error handling behavior

**Module Dependencies:**
```
main.py
├── rocket_alert_api.py
│   └── requests (external)
└── message_manager.py
    ├── message_builder.py
    │   ├── polyline (external)
    │   └── requests (external)
    ├── telegram_bot.py
    │   └── telebot (pyTelegramBotAPI)
    └── mastodon_bot.py
        └── mastodon (Mastodon.py)
```

---

## Module Reference

### main.py

**Purpose:** Application entry point and event loop orchestration

**File Location:** `/home/amit/projects/rocketalert-bots/main.py`

#### Constants

```python
HEARTBEAT_FILE: Path = Path("/tmp/heartbeat")
```
- **Type:** `pathlib.Path`
- **Description:** Liveness probe heartbeat file location
- **Usage:** Written on every KEEP_ALIVE event for Kubernetes health checks

---

#### Functions

##### `dump_traceback(sig, frame)`

**Signature:**
```python
def dump_traceback(sig: int, frame: FrameType) -> None
```

**Description:** Signal handler for SIGUSR1 that dumps Python traceback to stdout

**Parameters:**
- `sig` (int): Signal number (expected: `signal.SIGUSR1`)
- `frame` (FrameType): Current stack frame

**Returns:** `None`

**Side Effects:**
- Prints traceback to stdout via `faulthandler.dump_traceback()`

**Usage Example:**
```bash
# Send SIGUSR1 to process to trigger traceback
docker exec <container-id> kill -USR1 1
# Traceback will appear in container logs
```

**Notes:**
- Registered in `main()` via `signal.signal(signal.SIGUSR1, dump_traceback)`
- Useful for debugging hung processes without restarting

---

##### `main()`

**Signature:**
```python
def main() -> None
```

**Description:** Main event loop that connects to RocketAlert API and processes events

**Returns:** `None` (runs indefinitely or until `KeyboardInterrupt`)

**Flow:**
1. Enable fault handler for crash diagnostics
2. Register SIGUSR1 signal handler
3. Initialize `MessageManager` (creates bot instances)
4. Enter infinite loop:
   - Connect to SSE stream via `RocketAlertAPI().listenToServerEvents()`
   - Iterate over SSE lines
   - Parse JSON events
   - Filter KEEP_ALIVE events (update heartbeat)
   - Process real alerts via `messageManager.postMessage()`
   - Handle exceptions and reconnect

**Exception Handling:**

| Exception | Behavior |
|-----------|----------|
| `KeyboardInterrupt` | Print termination message, exit with code 1 |
| `requests.exceptions.ReadTimeout` | Log timeout, reconnect immediately |
| `requests.exceptions.ConnectionError` | Log error, sleep 5s, reconnect |
| `json.JSONDecodeError` | Log error, skip event, continue |
| `requests.exceptions.ChunkedEncodingError` | Log error, reconnect immediately |
| Generic `Exception` | Log error, sleep 5s, reconnect |

**Usage Example:**
```python
if __name__ == "__main__":
    main()  # Runs indefinitely
```

**Notes:**
- **Blocking:** This function never returns under normal operation
- **Reconnect Logic:** Always attempts to reconnect (never exits on errors)
- **Heartbeat:** Updates `/tmp/heartbeat` every 20s (KEEP_ALIVE interval)

---

### rocket_alert_api.py

**Purpose:** SSE client for RocketAlert API connection

**File Location:** `/home/amit/projects/rocketalert-bots/rocket_alert_api.py`

#### Class: `RocketAlertAPI`

##### `__init__()`

**Signature:**
```python
def __init__(self) -> None
```

**Description:** Initialize API client with environment variables and headers

**Raises:**
- `KeyError` - If required environment variables are missing:
  - `RA_BASEURL`
  - `CUSTOM_HEADER_KEY`
  - `CUSTOM_HEADER_VALUE`

**Attributes Set:**
- `self.baseURL` (str): Base URL for RocketAlert API
- `self.customHeaderValue` (str): Custom authentication header value
- `self.customHeaderKey` (str): Custom authentication header name
- `self.headers` (dict): HTTP headers for requests

**Usage Example:**
```python
# Requires environment variables to be set
api = RocketAlertAPI()
print(api.baseURL)  # https://ra-agg.kipodopik.com/api/v2/alerts
```

**Notes:**
- Values are stripped of whitespace via `.strip()`
- Missing environment variables will crash on initialization (fail-fast)

---

##### `listenToServerEvents()`

**Signature:**
```python
def listenToServerEvents(self) -> requests.Response
```

**Description:** Establish SSE connection to RocketAlert API

**Returns:**
- `requests.Response`: Streaming response object with SSE data

**Response Properties:**
- `response.iter_lines(decode_unicode=True)`: Generator yielding SSE lines
- `response.encoding`: Set to `'utf-8'` by caller (main.py)
- `response.status_code`: HTTP status (200 on success)

**Request Details:**
- **URL:** `{baseURL}/real-time?alertTypeId=-1`
- **Method:** GET
- **Stream:** `True` (enables SSE streaming)
- **Timeout:** `(10, 60)` - 10s connect, 60s read
- **Headers:**
  - Custom auth header (e.g., `X-SECURITY-TOKEN: <value>`)
  - `User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/81.0`

**Usage Example:**
```python
api = RocketAlertAPI()
with api.listenToServerEvents() as response:
    response.encoding = 'utf-8'
    for line in response.iter_lines(decode_unicode=True):
        if line.strip():
            event = json.loads(line.lstrip("data:"))
            print(event)
```

**Raises:**
- `requests.exceptions.Timeout` - If connection or read timeout exceeded
- `requests.exceptions.ConnectionError` - If network unavailable
- `requests.exceptions.HTTPError` - If API returns 4xx/5xx status

**Notes:**
- **Query Parameter:** `alertTypeId=-1` retrieves all alert types
- **Timeout Rationale:** 60s read timeout is 3× keep-alive interval (20s)
- **User-Agent:** Firefox string bypasses Cloudflare bot detection

---

### message_manager.py

**Purpose:** Orchestrate alert processing and bot message distribution

**File Location:** `/home/amit/projects/rocketalert-bots/message_manager.py`

#### Class: `MessageManager`

##### `__init__()`

**Signature:**
```python
def __init__(self) -> None
```

**Description:** Initialize message manager with bot instances and message builder

**Attributes Set:**
- `self.mapFileCount` (int): Counter for map file naming (unused, legacy)
- `self.MAP_MAX_REQUEST_LENGTH` (int): Mapbox URL length limit (8192 chars, unused)
- `self.messageBuilder` (AlertMessageBuilder): Message formatter instance
- `self.telegramBot` (TelegramBot): Telegram bot instance
- `self.mastodonBot` (MastodonBot): Mastodon bot instance

**Side Effects:**
- Prints initialization debug messages to stdout
- Initializes bot connections (may exit if credentials invalid)

**Usage Example:**
```python
manager = MessageManager()
# Bots are now ready to send messages
```

**Notes:**
- Constructor may block for 1-2 seconds during bot initialization
- Telegram initialization validates token via `get_me()` API call

---

##### `postMessage(eventData)`

**Signature:**
```python
def postMessage(self, eventData: dict) -> None
```

**Description:** Process event data and post messages to all bots

**Parameters:**
- `eventData` (dict): Event data structure containing:
  - `"alerts"` (list[dict]): Array of alert objects
  - `"alertTypeId"` (int): Type of alert (1=Rocket, 2=UAV, else=Red)

**Returns:** `None`

**Flow:**
1. Extract alerts array from event data
2. Normalize single alert to list (if not already)
3. Extract alert metadata (type ID, timestamp)
4. For each alert:
   - Format location string via `messageBuilder.buildAlert()`
   - Append to `alertLocations` buffer
5. Build final message via `messageBuilder.buildMessage()`
6. Post to Telegram and Mastodon (sequential)

**Usage Example:**
```python
event_data = {
    "alertTypeId": 1,
    "alerts": [
        {
            "name": "נירים",
            "englishName": "Nirim",
            "areaNameHe": "עוטף עזה",
            "areaNameEn": "Gaza Envelope",
            "timeStamp": "2023-12-04 16:59:09",
            # ... other fields
        }
    ]
}

manager = MessageManager()
manager.postMessage(event_data)
# Messages posted to Telegram and Mastodon
```

**Error Handling:**
- Wraps bot posting in `try/except Exception` to prevent single bot failure from blocking others
- Logs errors but continues processing

**Notes:**
- **Map Generation:** Lines 36-60 contain commented-out static map logic
- **Message Batching:** Single `buildMessage()` call for all alerts in event

---

### message_builder.py

**Purpose:** Format alert data into human-readable messages

**File Location:** `/home/amit/projects/rocketalert-bots/message_builder.py`

#### Class: `AlertMessageBuilder`

##### `__init__()`

**Signature:**
```python
def __init__(self) -> None
```

**Description:** Initialize message builder with Mapbox credentials and polygon data

**Attributes Set:**
- `self.accessToken` (str): Mapbox API token (from `MAPBOX_TOKEN` env var)
- `self.strokeColor` (str): Polygon stroke color (`"ff0000"` - red)
- `self.strokeFill` (str): Polygon fill color (`"bb1b1b"` - dark red)
- `self.styleId` (str): Mapbox style ID (`"dark-v11"`)
- `self.mapFile` (str): Map filename prefix (`"tmp_static_map"`)
- `self.polygons` (dict | None): Loaded polygon data or `None` if load fails

**Raises:**
- `KeyError` - If `MAPBOX_TOKEN` environment variable missing

**Usage Example:**
```python
builder = AlertMessageBuilder()
print(builder.polygons is None)  # True (unless polygons.json exists)
```

**Notes:**
- Attempts to load `polygons.json` from current directory
- Fails gracefully if file missing (sets `self.polygons = None`)

---

##### `buildAlert(alert)`

**Signature:**
```python
def buildAlert(self, alert: dict) -> str
```

**Description:** Format single alert location as "Name (Area)" string

**Parameters:**
- `alert` (dict): Alert object containing:
  - `"name"` (str): Hebrew location name
  - `"englishName"` (str | None): English location name
  - `"areaNameHe"` (str | None): Hebrew area name
  - `"areaNameEn"` (str | None): English area name

**Returns:**
- `str`: Formatted location string in one of these formats:
  - `"EnglishName (EnglishArea)"` - Both English names available
  - `"EnglishName (HebrewArea)"` - Only English name available
  - `"HebrewName (Area)"` - Only Hebrew name available
  - `"Name"` - No area name available

**Logic:**
```python
name = alert["englishName"] or alert["name"]  # English preferred
areaName = alert["areaNameEn"] or alert["areaNameHe"]  # English preferred

if areaName is None:
    return name
return f"{name} ({areaName})"
```

**Usage Example:**
```python
alert = {
    "name": "נירים",
    "englishName": "Nirim",
    "areaNameHe": "עוטף עזה",
    "areaNameEn": "Gaza Envelope"
}

builder = AlertMessageBuilder()
location = builder.buildAlert(alert)
print(location)  # "Nirim (Gaza Envelope)"
```

**Edge Cases:**
- If both names are `None`, returns `None` (caller should handle)
- If area names are empty strings, treated as `None` (falsy)

---

##### `buildMessageText(alertTypeId, timestamp, alertLocations)`

**Signature:**
```python
def buildMessageText(self, alertTypeId: int, timestamp: str, alertLocations: str) -> str
```

**Description:** Build complete message text with header and location list

**Parameters:**
- `alertTypeId` (int): Type of alert
  - `1` → "Rocket alert"
  - `2` → "Hostile UAV alert"
  - Other → "Red alert"
- `timestamp` (str): Event timestamp (e.g., `"2023-12-04 16:59:09"`)
- `alertLocations` (str): Newline-separated list of formatted locations

**Returns:**
- `str`: Formatted message text:
  ```
  [Alert Type] [Timestamp]:

  [Location 1]
  [Location 2]
  ...

  ```

**Usage Example:**
```python
builder = AlertMessageBuilder()
text = builder.buildMessageText(
    alertTypeId=1,
    timestamp="2023-12-04 16:59:09",
    alertLocations="Nirim (Gaza Envelope)\nKfar Aza (Gaza Envelope)\n"
)
print(text)
# Rocket alert 2023-12-04 16:59:09:
#
# Nirim (Gaza Envelope)
# Kfar Aza (Gaza Envelope)
#
```

**Notes:**
- Two newlines after header for visual separation
- One trailing newline after locations

---

##### `buildMessage(staticMap, mapFileCount, alertTypeId, timestamp, alertLocations)`

**Signature:**
```python
def buildMessage(
    self,
    staticMap: dict,
    mapFileCount: int,
    alertTypeId: int,
    timestamp: str,
    alertLocations: str
) -> dict
```

**Description:** Build message dictionary with text and map file (map generation disabled)

**Parameters:**
- `staticMap` (dict): Map overlay data (unused, legacy)
  - `"overlays"` (list[str]): Polygon overlays
  - `"markers"` (list[str]): Map markers
- `mapFileCount` (int): Map file index (unused, legacy)
- `alertTypeId` (int): Alert type ID
- `timestamp` (str): Event timestamp
- `alertLocations` (str): Formatted location list

**Returns:**
- `dict`: Message dictionary
  - `"text"` (str): Message text content
  - ~~`"file"` (str): Map filename (removed in current version)~~

**Usage Example:**
```python
builder = AlertMessageBuilder()
message = builder.buildMessage(
    staticMap={"overlays": [], "markers": []},
    mapFileCount=0,
    alertTypeId=1,
    timestamp="2023-12-04 16:59:09",
    alertLocations="Nirim (Gaza Envelope)\n"
)
print(message)
# {"text": "Rocket alert 2023-12-04 16:59:09:\n\nNirim (Gaza Envelope)\n\n"}
```

**Side Effects:**
- Prints message text to stdout (lines 102-105)

**Notes:**
- Map generation code commented out (lines 96-98)
- Returns only text, no file reference

---

##### `buildPolygonOverlay(alert)` (Disabled)

**Signature:**
```python
def buildPolygonOverlay(self, alert: dict) -> str | None
```

**Description:** Generate Mapbox polygon overlay for alert location

**Status:** ⚠️ Functional but unused (map generation disabled)

**Parameters:**
- `alert` (dict): Alert object with `"taCityId"` (int) for polygon lookup

**Returns:**
- `str`: URL-encoded polygon overlay string
- `None`: If polygons not loaded or city ID not found

**Notes:**
- Requires `polygons.json` to be loaded
- Uses polyline encoding for compact representation

---

##### `buildMarker(alert)`

**Signature:**
```python
def buildMarker(self, alert: dict) -> str
```

**Description:** Generate Mapbox marker for alert coordinates

**Status:** ⚠️ Functional but unused (map generation disabled)

**Parameters:**
- `alert` (dict): Alert object with:
  - `"lat"` (float): Latitude
  - `"lon"` (float): Longitude

**Returns:**
- `str`: Mapbox marker string (e.g., `"pin-s+ff0000(34.3941,31.3357)"`)

**Notes:**
- Marker color: Red (`ff0000`)
- Marker size: Small (`pin-s`)

---

### telegram_bot.py

**Purpose:** Post messages to Telegram channel

**File Location:** `/home/amit/projects/rocketalert-bots/telegram_bot.py`

#### Constants

```python
MAX_CHARACTERS: int = 4096
TELEGRAM_FOOTER: str = "[RocketAlert.live](https://RocketAlert.live)"
```

**Description:**
- `MAX_CHARACTERS`: Telegram's message length limit
- `TELEGRAM_FOOTER`: Markdown link appended to all messages

---

#### Class: `TelegramBot`

##### `__init__()`

**Signature:**
```python
def __init__(self) -> None
```

**Description:** Initialize Telegram bot with token authentication

**Environment Variables Required:**
- `TELEGRAM_BOT_TOKEN` (str): Bot token from @BotFather
- `TELEGRAM_CHANNEL_ID` (str, optional): Channel username (default: `@RocketAlert`)

**Attributes Set:**
- `self.bot_token` (str): Bot authentication token
- `self.channel` (str): Target channel username
- `self.bot` (TeleBot): pyTelegramBotAPI client instance

**Raises:**
- `SystemExit(1)` - If `TELEGRAM_BOT_TOKEN` missing or bot connection fails

**Side Effects:**
- Prints debug messages to stdout
- Calls `get_me()` to validate bot token

**Usage Example:**
```python
# Requires TELEGRAM_BOT_TOKEN environment variable
bot = TelegramBot()
# Bot is now authenticated and connected
```

**Notes:**
- Exit on failure is intentional (fail-fast deployment)
- Connection test prevents runtime failures

---

##### `sendMessage(content)`

**Signature:**
```python
def sendMessage(self, content: str) -> None
```

**Description:** Send message to Telegram channel with automatic truncation

**Parameters:**
- `content` (str): Message text to send

**Returns:** `None`

**Behavior:**
1. Append `TELEGRAM_FOOTER` to content
2. If length > 4096, call `truncateToMaxMessageSize()`
3. Normalize to list (if single string)
4. Post each message via `bot.send_message()`
5. Log errors but don't raise

**Message Format:**
- Parse mode: `Markdown`
- Link preview: Disabled
- Channel: `self.channel` (e.g., `@RocketAlert`)

**Usage Example:**
```python
bot = TelegramBot()
bot.sendMessage("Rocket alert 16:59:09:\n\nNirim (Gaza Envelope)")
# Message posted to @RocketAlert channel
```

**Error Handling:**
- Catches all exceptions, prints error, continues execution
- Does not re-raise (fail-safe behavior)

**Side Effects:**
- Prints "To Telegram...done." to stdout

---

##### `truncateToMaxMessageSize(content)`

**Signature:**
```python
def truncateToMaxMessageSize(self, content: str) -> list[str]
```

**Description:** Split oversized message into multiple sub-messages on line boundaries

**Parameters:**
- `content` (str): Message text exceeding 4096 characters

**Returns:**
- `list[str]`: List of messages, each < 4096 characters

**Algorithm:**
1. Initialize empty message buffer
2. For each line in content:
   - If adding line keeps message < 4096: append line
   - Else: save current message, start new message with current line
3. Append final message buffer

**Usage Example:**
```python
bot = TelegramBot()
long_message = "Location\n" * 300  # ~3000 chars
messages = bot.truncateToMaxMessageSize(long_message)
print(len(messages))  # 1 (fits in single message)

very_long = "Location\n" * 500  # ~5000 chars
messages = bot.truncateToMaxMessageSize(very_long)
print(len(messages))  # 2 (split into multiple)
```

**Edge Cases:**
- Single line > 4096 chars: Creates message with that line only (will exceed limit)
- Empty content: Returns empty list

**Notes:**
- Preserves line integrity (never splits mid-line)
- Footer is included in initial content before truncation

---

### mastodon_bot.py

**Purpose:** Post messages to Mastodon instance

**File Location:** `/home/amit/projects/rocketalert-bots/mastodon_bot.py`

#### Constants

```python
MAX_CHARACTERS: int = 500
```

**Description:** Mastodon's toot character limit (stricter than Telegram)

---

#### Class: `MastodonBot`

##### `__init__()`

**Signature:**
```python
def __init__(self) -> None
```

**Description:** Initialize Mastodon bot with OAuth2 access token

**Environment Variables Required:**
- `MASTO_BASEURL` (str): Mastodon instance URL (e.g., `https://mastodon.social`)
- `MASTO_ACCESS_TOKEN` (str): OAuth2 access token

**Attributes Set:**
- `self.api_baseurl` (str): Mastodon instance URL
- `self.accessToken` (str): OAuth2 access token
- `self.mastodon` (Mastodon): Mastodon.py client instance

**Client Configuration:**
- `request_timeout`: 30 seconds (prevents hanging on slow instances)

**Raises:**
- `KeyError` - If environment variables missing

**Usage Example:**
```python
bot = MastodonBot()
# Bot is now authenticated to mastodon.social
```

**Notes:**
- No connection validation on initialization (unlike Telegram)
- Timeout tunable via constructor argument

---

##### `sendMessage(content)`

**Signature:**
```python
def sendMessage(self, content: str) -> None
```

**Description:** Send message to Mastodon instance with automatic truncation

**Parameters:**
- `content` (str): Message text to send

**Returns:** `None`

**Behavior:**
1. If length > 500, call `truncateToMaxMessageSize()`
2. Normalize to list (if single string)
3. Post each message via `mastodon.status_post()`
4. Log errors but don't raise

**Message Format:**
- Visibility: Public (default)
- Content type: Plain text
- Media: None (disabled, lines 27-34)

**Usage Example:**
```python
bot = MastodonBot()
bot.sendMessage("Rocket alert 16:59:09:\n\nNirim")
# Message posted to Mastodon timeline
```

**Error Handling:**
- Catches all exceptions, prints error
- `finally` block ensures "done." is always printed

**Side Effects:**
- Prints "To Mastodon...done." to stdout (even on error)

**Notes:**
- No footer added (unlike Telegram)
- Media posting commented out (lines 29-34)

---

##### `truncateToMaxMessageSize(content)`

**Signature:**
```python
def truncateToMaxMessageSize(self, content: str) -> list[str]
```

**Description:** Split oversized message into multiple sub-messages on line boundaries

**Parameters:**
- `content` (str): Message text exceeding 500 characters

**Returns:**
- `list[str]`: List of messages, each < 500 characters

**Bug:** ⚠️ Line 52 has bug - should be `newMessage = f"{line}\n"` instead of `newMessage = ""`

**Current Behavior:**
- Lines exceeding limit are **dropped** instead of starting new message

**Usage Example:**
```python
bot = MastodonBot()
long_message = "Location\n" * 60  # ~600 chars
messages = bot.truncateToMaxMessageSize(long_message)
# Bug: Last ~100 chars dropped instead of creating 2nd message
```

**Corrected Algorithm (intended):**
```python
def truncateToMaxMessageSize(self, content):
    truncatedMessages = []
    newMessage = ""
    for line in content.splitlines():
        if len(newMessage) + len(line) + 1 < MAX_CHARACTERS:
            newMessage += f"{line}\n"
        else:
            if newMessage:
                truncatedMessages.append(newMessage)
            newMessage = f"{line}\n"  # Fix: Start new message with current line
    if newMessage:
        truncatedMessages.append(newMessage)
    return truncatedMessages
```

---

## Configuration Reference

### Application Configuration

The system is configured entirely via environment variables (no config files).

**Configuration Sources:**
1. **Local Development:** `.env` file or shell exports
2. **Docker:** `-e` flags or `--env-file`
3. **Kubernetes:** ConfigMap or Secret mounted as environment variables

**Required Variables:**

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `RA_BASEURL` | URL | RocketAlert API base URL | `https://ra-agg.kipodopik.com/api/v2/alerts` |
| `CUSTOM_HEADER_KEY` | String | Custom auth header name | `X-SECURITY-TOKEN` |
| `CUSTOM_HEADER_VALUE` | String | Custom auth header value | `VWqBnCLBmm93MJVhGbxocIEo1JyJYOPp` |
| `TELEGRAM_BOT_TOKEN` | String | Telegram bot token | `8271024720:AAFrkR15ix...` |
| `MASTO_BASEURL` | URL | Mastodon instance URL | `https://mastodon.social` |
| `MASTO_ACCESS_TOKEN` | String | Mastodon OAuth2 token | `x1C8wV94MO5vCbdjEE6C...` |
| `MAPBOX_TOKEN` | String | Mapbox API token (unused) | `pk.eyJ1Ijoi...` |

**Optional Variables:**

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `TELEGRAM_CHANNEL_ID` | String | `@RocketAlert` | Telegram channel username |
| `COMMIT_SHA` | String | `"unknown"` | Git commit SHA for version tracking |
| `TZ` | String | System default | Timezone (e.g., `America/New_York`) |

**Validation:**
- Missing required variables cause immediate exit (`KeyError` or `SystemExit(1)`)
- Values are stripped of whitespace via `.strip()`
- No default values for security-sensitive variables

---

## Environment Variables

### Detailed Variable Reference

#### `RA_BASEURL`

**Purpose:** RocketAlert API base URL for SSE connection

**Type:** `str` (URL)

**Required:** Yes

**Format:** `https://hostname/path` (no trailing slash)

**Used By:** `rocket_alert_api.py:6`

**Example:**
```bash
export RA_BASEURL="https://ra-agg.kipodopik.com/api/v2/alerts"
```

**Notes:**
- Endpoint path `/real-time?alertTypeId=-1` is appended
- Must be HTTPS (no HTTP support)

---

#### `CUSTOM_HEADER_KEY` & `CUSTOM_HEADER_VALUE`

**Purpose:** Custom HTTP header for RocketAlert API authentication

**Type:** `str`

**Required:** Yes

**Used By:** `rocket_alert_api.py:7-8`

**Example:**
```bash
export CUSTOM_HEADER_KEY="X-SECURITY-TOKEN"
export CUSTOM_HEADER_VALUE="VWqBnCLBmm93MJVhGbxocIEo1JyJYOPp"
```

**Security:**
- Value is redacted in debug logs (line 20)
- Transmitted over HTTPS only
- Should be rotated periodically

---

#### `TELEGRAM_BOT_TOKEN`

**Purpose:** Telegram Bot API authentication token

**Type:** `str`

**Required:** Yes

**Format:** `{bot_id}:{random_token}` (e.g., `8271024720:AAFrkR15ix...`)

**Used By:** `telegram_bot.py:11`

**Obtaining Token:**
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` command
3. Follow prompts to create bot
4. Copy token from BotFather's response

**Example:**
```bash
export TELEGRAM_BOT_TOKEN="8271024720:AAFrkR15ixUljp4nDVWLaLVZKFLZDBazd8I"
```

**Security:**
- Token grants full bot control (send messages, read chat info)
- Never commit to git
- Revoke via BotFather if leaked

---

#### `TELEGRAM_CHANNEL_ID`

**Purpose:** Target Telegram channel for message posting

**Type:** `str`

**Required:** No (default: `@RocketAlert`)

**Format:** `@username` or chat ID (negative integer)

**Used By:** `telegram_bot.py:16`

**Example:**
```bash
export TELEGRAM_CHANNEL_ID="@RocketAlert"
# or
export TELEGRAM_CHANNEL_ID="-1001234567890"
```

**Requirements:**
- Bot must be admin of channel
- Channel must exist and be accessible

---

#### `MASTO_BASEURL`

**Purpose:** Mastodon instance URL

**Type:** `str` (URL)

**Required:** Yes

**Format:** `https://hostname` (no trailing slash)

**Used By:** `mastodon_bot.py:9`

**Example:**
```bash
export MASTO_BASEURL="https://mastodon.social"
```

**Notes:**
- Works with any Mastodon-compatible instance
- Must be HTTPS

---

#### `MASTO_ACCESS_TOKEN`

**Purpose:** Mastodon OAuth2 access token

**Type:** `str`

**Required:** Yes

**Scope Required:** `write:statuses`

**Used By:** `mastodon_bot.py:10`

**Obtaining Token:**
1. Log into Mastodon instance
2. Go to Settings → Development → New Application
3. Name: "RocketAlert Bots"
4. Scopes: `write:statuses`
5. Submit → Copy access token

**Example:**
```bash
export MASTO_ACCESS_TOKEN="x1C8wV94MO5vCbdjEE6CjdifprKVydPNYbzFFK0TCFI"
```

**Security:**
- Token limited to posting (cannot read DMs or delete posts)
- Revoke via Mastodon settings if leaked

---

#### `MAPBOX_TOKEN`

**Purpose:** Mapbox API token for static map generation

**Type:** `str`

**Required:** Yes (but unused in current version)

**Used By:** `message_builder.py:9`

**Status:** ⚠️ Required for initialization but not used (map generation disabled)

**Example:**
```bash
export MAPBOX_TOKEN="pk.eyJ1IjoiZXJlem5hZ2FyIiwiYSI6ImNsb2pmcXV4ZzFreXgyam8zdjdvdWtqMHMifQ.e2E4pq7dQZL7_YszHD25kA"
```

**Notes:**
- Can use dummy value if map generation remains disabled
- Required to prevent `KeyError` on startup

---

#### `COMMIT_SHA`

**Purpose:** Git commit SHA for version tracking

**Type:** `str`

**Required:** No (default: `"unknown"`)

**Used By:** `main.py:27`

**Set By:** Docker build argument

**Example:**
```bash
docker build --build-arg COMMIT_SHA=$(git rev-parse HEAD) -t myimage .
```

**Usage:**
- Printed on startup: `Starting version: abc123def456`
- Useful for debugging deployed versions

---

#### `TZ`

**Purpose:** Timezone for log timestamps

**Type:** `str`

**Required:** No (default: UTC)

**Format:** IANA timezone name (e.g., `America/New_York`)

**Used By:** System (affects `datetime.now()`)

**Example:**
```bash
export TZ="America/New_York"
```

**Notes:**
- Set in Dockerfile (line 13)
- Affects all timestamp outputs

---

## Data Structures

### Event Data Structure

**Type:** `dict`

**Description:** SSE event from RocketAlert API

**Schema:**
```python
{
    "alertTypeId": int,  # 1=Rocket, 2=UAV, else=Red alert
    "alerts": [
        {
            "name": str,              # Hebrew location name
            "englishName": str | None,  # English location name
            "lat": float,             # Latitude
            "lon": float,             # Longitude
            "taCityId": int,          # City ID for polygon lookup
            "countdownSec": int,      # Shelter countdown time
            "areaNameHe": str | None, # Hebrew area name
            "areaNameEn": str | None, # English area name
            "timeStamp": str          # "YYYY-MM-DD HH:MM:SS"
        },
        # ... more alerts
    ]
}
```

**Example:**
```json
{
  "alertTypeId": 1,
  "alerts": [
    {
      "name": "נירים",
      "englishName": "Nirim",
      "lat": 31.3357,
      "lon": 34.3941,
      "taCityId": 171,
      "countdownSec": 15,
      "areaNameHe": "עוטף עזה",
      "areaNameEn": "Gaza Envelope",
      "timeStamp": "2023-12-04 16:59:09"
    }
  ]
}
```

---

### Message Dictionary

**Type:** `dict`

**Description:** Formatted message ready for posting

**Schema:**
```python
{
    "text": str,  # Formatted message text
    # "file": str  # Map filename (removed in v2.0)
}
```

**Example:**
```python
{
    "text": "Rocket alert 2023-12-04 16:59:09:\n\nNirim (Gaza Envelope)\n\n"
}
```

---

### Static Map Data (Unused)

**Type:** `dict`

**Description:** Map overlay data for Mapbox static maps

**Schema:**
```python
{
    "overlays": list[str],  # Polygon overlay strings
    "markers": list[str]    # Marker position strings
}
```

**Example:**
```python
{
    "overlays": ["path+ff0000+bb1b1b(encoded_polyline)"],
    "markers": ["pin-s+ff0000(34.3941,31.3357)"]
}
```

**Status:** ⚠️ Unused (map generation disabled)

---

## Constants

### Character Limits

```python
# telegram_bot.py
MAX_CHARACTERS: int = 4096  # Telegram message limit
TELEGRAM_FOOTER: str = "[RocketAlert.live](https://RocketAlert.live)"  # 43 chars

# mastodon_bot.py
MAX_CHARACTERS: int = 500  # Mastodon toot limit
```

### Timeout Values

```python
# rocket_alert_api.py
CONNECT_TIMEOUT: int = 10  # seconds (connect phase)
READ_TIMEOUT: int = 60     # seconds (read phase)

# mastodon_bot.py
REQUEST_TIMEOUT: int = 30  # seconds (Mastodon API calls)
```

### Heartbeat Configuration

```python
# main.py
HEARTBEAT_FILE: Path = Path("/tmp/heartbeat")

# Kubernetes liveness probe (bots-namespace.yaml)
KEEP_ALIVE_INTERVAL: int = 20  # seconds (SSE server)
HEARTBEAT_THRESHOLD: int = 90  # seconds (Kubernetes probe)
```

### Backoff Delays

```python
# main.py exception handlers
CONNECTION_ERROR_BACKOFF: int = 5  # seconds
GENERIC_ERROR_BACKOFF: int = 5     # seconds
TIMEOUT_BACKOFF: int = 0           # immediate reconnect
```

---

## Error Codes

### Exit Codes

| Code | Meaning | Source |
|------|---------|--------|
| 0 | Clean shutdown (unused) | - |
| 1 | Keyboard interrupt or bot init failure | `main.py:56`, `telegram_bot.py:14` |

### HTTP Status Codes

**From RocketAlert API:**
- `200 OK` - SSE connection established
- `401 Unauthorized` - Invalid `CUSTOM_HEADER_VALUE`
- `403 Forbidden` - Cloudflare block (User-Agent issue)
- `503 Service Unavailable` - API server down

**From Telegram Bot API:**
- `200 OK` - Message posted successfully
- `400 Bad Request` - Invalid message format
- `401 Unauthorized` - Invalid bot token
- `403 Forbidden` - Bot not admin of channel
- `429 Too Many Requests` - Rate limit exceeded

**From Mastodon API:**
- `200 OK` - Toot posted successfully
- `401 Unauthorized` - Invalid access token
- `403 Forbidden` - Insufficient scope
- `422 Unprocessable Entity` - Validation error (e.g., message too long)

---

## Usage Examples

### Complete Application Flow

```python
import os
import json
from datetime import datetime
from pathlib import Path

# Set environment variables
os.environ.update({
    "RA_BASEURL": "https://ra-agg.kipodopik.com/api/v2/alerts",
    "CUSTOM_HEADER_KEY": "X-SECURITY-TOKEN",
    "CUSTOM_HEADER_VALUE": "secret_value",
    "TELEGRAM_BOT_TOKEN": "123456:ABC-DEF",
    "TELEGRAM_CHANNEL_ID": "@TestChannel",
    "MASTO_BASEURL": "https://mastodon.social",
    "MASTO_ACCESS_TOKEN": "access_token",
    "MAPBOX_TOKEN": "pk.mapbox_token"
})

# Initialize components
from rocket_alert_api import RocketAlertAPI
from message_manager import MessageManager

manager = MessageManager()
api = RocketAlertAPI()

# Event loop (simplified)
HEARTBEAT_FILE = Path("/tmp/heartbeat")

with api.listenToServerEvents() as response:
    response.encoding = "utf-8"
    for line in response.iter_lines(decode_unicode=True):
        if not line.strip():
            continue

        line = line.lstrip("data:")
        event_data = json.loads(line)

        # Filter keep-alive events
        if "KEEP_ALIVE" in event_data["alerts"][0].get("name", ""):
            HEARTBEAT_FILE.write_text(str(datetime.now().timestamp()))
            continue

        # Process real alerts
        print(f"{datetime.now()} - Processing event...")
        manager.postMessage(event_data)
        print(f"{datetime.now()} - Event processed.")
```

---

### Manual Message Building

```python
from message_builder import AlertMessageBuilder

# Initialize builder
builder = AlertMessageBuilder()

# Single alert
alert = {
    "name": "נירים",
    "englishName": "Nirim",
    "areaNameHe": "עוטף עזה",
    "areaNameEn": "Gaza Envelope",
    "lat": 31.3357,
    "lon": 34.3941,
    "taCityId": 171,
    "timeStamp": "2023-12-04 16:59:09"
}

# Format location
location = builder.buildAlert(alert)
print(location)  # "Nirim (Gaza Envelope)"

# Build complete message
message = builder.buildMessage(
    staticMap={"overlays": [], "markers": []},
    mapFileCount=0,
    alertTypeId=1,
    timestamp="2023-12-04 16:59:09",
    alertLocations=f"{location}\n"
)

print(message["text"])
# Rocket alert 2023-12-04 16:59:09:
#
# Nirim (Gaza Envelope)
#
```

---

### Direct Bot Usage

```python
from telegram_bot import TelegramBot
from mastodon_bot import MastodonBot

# Initialize bots
telegram = TelegramBot()
mastodon = MastodonBot()

# Send message
message = "Rocket alert 16:59:09:\n\nNirim (Gaza Envelope)"

telegram.sendMessage(message)
# Posted to Telegram with footer: "[RocketAlert.live](https://RocketAlert.live)"

mastodon.sendMessage(message)
# Posted to Mastodon without footer
```

---

### Testing Truncation Logic

```python
from telegram_bot import TelegramBot

bot = TelegramBot()

# Test case 1: Message under limit
short_message = "Rocket alert:\n\nLocation 1\nLocation 2"
result = bot.sendMessage(short_message)
# Sends 1 message

# Test case 2: Message over limit
long_message = "Rocket alert:\n\n" + ("Location\n" * 500)  # ~5000 chars
result = bot.sendMessage(long_message)
# Sends 2 messages (split at line boundary)

# Manual truncation test
truncated = bot.truncateToMaxMessageSize(long_message)
print(len(truncated))  # 2
print(len(truncated[0]) < 4096)  # True
print(len(truncated[1]) < 4096)  # True
```

---

### Custom SSE Client

```python
from rocket_alert_api import RocketAlertAPI
import json

api = RocketAlertAPI()

# Custom event handler
def handle_event(event_data):
    alerts = event_data["alerts"]
    for alert in alerts:
        print(f"Alert: {alert['englishName']} at {alert['timeStamp']}")

# Listen to events
with api.listenToServerEvents() as response:
    response.encoding = "utf-8"
    for line in response.iter_lines(decode_unicode=True):
        if line.strip():
            event_data = json.loads(line.lstrip("data:"))
            if "KEEP_ALIVE" not in event_data["alerts"][0].get("name", ""):
                handle_event(event_data)
```

---

## Appendix

### Type Definitions (TypeScript-style)

```typescript
// For reference (Python uses runtime type checking)

type AlertType = 1 | 2 | number;  // 1=Rocket, 2=UAV, else=Red

interface Alert {
  name: string;
  englishName: string | null;
  lat: number;
  lon: number;
  taCityId: number;
  countdownSec: number;
  areaNameHe: string | null;
  areaNameEn: string | null;
  timeStamp: string;  // "YYYY-MM-DD HH:MM:SS"
}

interface EventData {
  alertTypeId: AlertType;
  alerts: Alert[];
}

interface Message {
  text: string;
  // file?: string;  // Removed in v2.0
}

interface StaticMapData {
  overlays: string[];
  markers: string[];
}
```

### Dependency Versions

```
# Core dependencies
requests==2.32.5
pytelegrambotapi==4.14.0
mastodon-py==2.1.4
polyline==2.0.4

# Testing dependencies
pytest==9.0.2
pytest-asyncio==1.3.0
pytest-cov==7.0.0
pytest-mock==3.15.1
coverage[toml]==7.13.0
responses==0.25.8
```

### Document Version

- **Version:** 1.0
- **Last Updated:** 2025-12-30
- **Covers:** RocketAlert Bots v2.0+
