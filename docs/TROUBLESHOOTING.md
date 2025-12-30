# RocketAlert Bots - Troubleshooting Guide

## Table of Contents

1. [Overview](#overview)
2. [Quick Diagnostics](#quick-diagnostics)
3. [Connection Issues](#connection-issues)
4. [Bot Posting Failures](#bot-posting-failures)
5. [Performance Problems](#performance-problems)
6. [Deployment Issues](#deployment-issues)
7. [Debug Logging](#debug-logging)
8. [Log Analysis](#log-analysis)
9. [Common Error Messages](#common-error-messages)
10. [Advanced Debugging](#advanced-debugging)

---

## Overview

This guide provides systematic troubleshooting procedures for the RocketAlert Bots system. Follow the quick diagnostics first, then drill down into specific problem areas.

**Troubleshooting Philosophy:**
1. **Gather Evidence:** Check logs, environment, network
2. **Isolate Problem:** Narrow down to specific component
3. **Test Fix:** Apply solution in non-production first
4. **Verify:** Confirm problem resolved

**Severity Levels:**

| Level | Impact | Response Time | Examples |
|-------|--------|---------------|----------|
| 🔴 Critical | No alerts posted | Immediate | SSE connection down, bot authentication failed |
| 🟡 Warning | Partial functionality | < 1 hour | One bot failing, high latency |
| 🟢 Info | Minor issues | Best effort | Truncated messages, cosmetic formatting |

---

## Quick Diagnostics

### Health Check Script

```bash
#!/bin/bash
# health-check.sh - Quick system health verification

echo "=== RocketAlert Bots Health Check ==="

# 1. Check if process running
if pgrep -f "python main.py" > /dev/null; then
    echo "✅ Process running (PID: $(pgrep -f 'python main.py'))"
else
    echo "❌ Process NOT running"
    exit 1
fi

# 2. Check heartbeat file (Kubernetes deployment)
if [ -f /tmp/heartbeat ]; then
    LAST=$(cat /tmp/heartbeat)
    NOW=$(date +%s)
    DIFF=$((NOW - ${LAST%.*}))
    if [ $DIFF -lt 90 ]; then
        echo "✅ Heartbeat recent (${DIFF}s ago)"
    else
        echo "❌ Heartbeat stale (${DIFF}s ago) - Process may be stuck"
        exit 1
    fi
else
    echo "⚠️  Heartbeat file not found (expected in K8s only)"
fi

# 3. Check environment variables
REQUIRED_VARS=("RA_BASEURL" "CUSTOM_HEADER_KEY" "CUSTOM_HEADER_VALUE" "TELEGRAM_BOT_TOKEN" "MASTO_BASEURL" "MASTO_ACCESS_TOKEN")
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Missing environment variable: $var"
        exit 1
    else
        echo "✅ $var is set"
    fi
done

# 4. Check network connectivity
if curl -s --max-time 5 https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe > /dev/null; then
    echo "✅ Telegram API reachable"
else
    echo "❌ Cannot reach Telegram API"
    exit 1
fi

if curl -s --max-time 5 ${MASTO_BASEURL}/api/v1/instance > /dev/null; then
    echo "✅ Mastodon API reachable"
else
    echo "❌ Cannot reach Mastodon API"
    exit 1
fi

# 5. Check recent logs for errors
if tail -100 /var/log/rocketalert.log 2>/dev/null | grep -i "error" > /dev/null; then
    echo "⚠️  Errors found in recent logs"
else
    echo "✅ No errors in recent logs"
fi

echo "=== Health check complete ==="
```

**Usage:**
```bash
chmod +x health-check.sh
./health-check.sh
```

### Kubernetes Health Check

```bash
# Check pod status
kubectl get pods -n bots -l app=rocketalert-bots

# Check recent events
kubectl get events -n bots --field-selector involvedObject.name=rocketalert-bots --sort-by='.lastTimestamp' | tail -20

# Check liveness probe status
kubectl describe pod -n bots -l app=rocketalert-bots | grep -A 10 "Liveness"

# Quick log check for errors
kubectl logs -n bots deployment/rocketalert-bots --tail=50 | grep -i error
```

---

## Connection Issues

### Problem: Cannot Connect to RocketAlert API

**Symptoms:**
```
DEBUG: Connecting to https://ra-agg.kipodopik.com/api/v2/alerts/real-time?alertTypeId=-1...
Connection error: HTTPSConnectionPool(host='ra-agg.kipodopik.com', port=443): Max retries exceeded
```

**Diagnosis Steps:**

1. **Test network connectivity:**
```bash
# Ping server
ping ra-agg.kipodopik.com

# Test HTTPS connection
curl -v https://ra-agg.kipodopik.com/api/v2/alerts/real-time?alertTypeId=-1 \
  -H "X-SECURITY-TOKEN: your_token_here" \
  -H "user-agent: Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/81.0"

# Expected: SSE stream starts (data: {...})
```

2. **Verify environment variables:**
```bash
echo "RA_BASEURL: $RA_BASEURL"
echo "CUSTOM_HEADER_KEY: $CUSTOM_HEADER_KEY"
echo "CUSTOM_HEADER_VALUE: ${CUSTOM_HEADER_VALUE:0:10}..." # Partial for security

# Verify no trailing slashes or spaces
python3 -c "import os; print(repr(os.environ['RA_BASEURL']))"
# Should print: 'https://ra-agg.kipodopik.com/api/v2/alerts' (no trailing slash)
```

3. **Check DNS resolution:**
```bash
nslookup ra-agg.kipodopik.com
dig ra-agg.kipodopik.com

# Try alternative DNS
nslookup ra-agg.kipodopik.com 8.8.8.8
```

4. **Test from inside container:**
```bash
# Docker
docker exec -it rocketalert-bots /bin/sh
curl https://ra-agg.kipodopik.com

# Kubernetes
kubectl exec -it -n bots deployment/rocketalert-bots -- /bin/sh
curl https://ra-agg.kipodopik.com
```

**Solutions:**

| Cause | Solution |
|-------|----------|
| DNS failure | Update DNS servers in container/pod |
| Firewall block | Whitelist `ra-agg.kipodopik.com:443` in egress rules |
| Invalid credentials | Verify `CUSTOM_HEADER_VALUE` with API provider |
| API server down | Contact API provider, check status page |
| TLS certificate issue | Update CA certificates: `apt-get update && apt-get install -y ca-certificates` |

**Kubernetes Network Policy Fix:**
```yaml
# If NetworkPolicy blocking egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: rocketalert-egress
  namespace: bots
spec:
  podSelector:
    matchLabels:
      app: rocketalert-bots
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector: {}  # Allow pod-to-pod
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 53  # DNS
  - to:
    - podSelector: {}
    ports:
    - protocol: TCP
      port: 443  # HTTPS
```

---

### Problem: SSE Connection Timeout

**Symptoms:**
```
Connection timeout (no data received in 60s), reconnecting...
```

**Diagnosis:**

1. **Check keep-alive interval:**
```bash
# Monitor SSE stream
curl -N https://ra-agg.kipodopik.com/api/v2/alerts/real-time?alertTypeId=-1 \
  -H "X-SECURITY-TOKEN: your_token" \
  -H "user-agent: Mozilla/5.0 ..." | \
  while IFS= read -r line; do
    echo "$(date '+%H:%M:%S') - $line"
  done

# Expected: KEEP_ALIVE events every 20 seconds
```

2. **Test timeout values:**
```python
# Temporarily increase timeout in rocket_alert_api.py
return requests.get(..., timeout=(10, 120))  # 2-minute read timeout
```

**Solutions:**

- **If keep-alive interval > 60s:** Increase read timeout in `rocket_alert_api.py:26`
- **If network unstable:** Add retry logic with exponential backoff
- **If proxy interference:** Bypass proxy or configure proxy to allow SSE

---

### Problem: Connection Refused (Port Blocked)

**Symptoms:**
```
Connection error: ('Connection aborted.', ConnectionRefusedError(111, 'Connection refused'))
```

**Diagnosis:**

```bash
# Test connectivity
telnet ra-agg.kipodopik.com 443

# Check local firewall
sudo iptables -L -n | grep 443

# Kubernetes: Check pod network
kubectl exec -n bots deployment/rocketalert-bots -- nc -zv ra-agg.kipodopik.com 443
```

**Solutions:**

- **Local firewall:** `sudo ufw allow out 443/tcp`
- **Corporate proxy:** Set `HTTP_PROXY` / `HTTPS_PROXY` environment variables
- **Kubernetes:** Verify no egress NetworkPolicy blocking port 443

---

## Bot Posting Failures

### Problem: Telegram Bot Authentication Failed

**Symptoms:**
```
CRITICAL ERROR: Failed to connect to Telegram: Unauthorized
```

**Diagnosis:**

1. **Verify token format:**
```bash
echo $TELEGRAM_BOT_TOKEN | grep -E '^[0-9]+:[A-Za-z0-9_-]+$'
# Should match: 8271024720:AAFrkR15ixUljp4nDVWLaLVZKFLZDBazd8I
```

2. **Test token directly:**
```bash
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"

# Expected response:
# {"ok":true,"result":{"id":8271024720,"is_bot":true,"first_name":"RocketAlert",...}}

# If error:
# {"ok":false,"error_code":401,"description":"Unauthorized"}
```

3. **Check token source:**
```bash
# Ensure no whitespace
python3 -c "import os; print(repr(os.environ['TELEGRAM_BOT_TOKEN']))"
# Should NOT have spaces: '8271024720:AAFrkR15...' (no '\n', ' ')
```

**Solutions:**

| Error | Fix |
|-------|-----|
| `Unauthorized` | Regenerate token via @BotFather (`/token` command) |
| Token has spaces/newlines | Strip whitespace: `TELEGRAM_BOT_TOKEN=$(echo $TELEGRAM_BOT_TOKEN | tr -d ' \n')` |
| Token revoked | Contact bot creator, regenerate via @BotFather |

---

### Problem: Telegram "Chat Not Found"

**Symptoms:**
```
Error posting message to Telegram: Chat not found
```

**Diagnosis:**

1. **Verify channel exists:**
```bash
# Check channel ID format
echo $TELEGRAM_CHANNEL_ID
# Should be: @RocketAlert (username) OR -1001234567890 (chat ID)

# Test message posting
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${TELEGRAM_CHANNEL_ID}" \
  -d "text=Test message"
```

2. **Verify bot is channel admin:**
```bash
# Check bot membership
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getChatMember?chat_id=${TELEGRAM_CHANNEL_ID}&user_id=8271024720"

# Expected: "status":"administrator"
```

**Solutions:**

- **Channel not found:** Verify `@RocketAlert` exists and is public/accessible
- **Bot not admin:** Add bot to channel, promote to admin
- **Chat ID incorrect:** Use [@raw_info_bot](https://t.me/raw_info_bot) to get correct channel ID

---

### Problem: Mastodon Authentication Failed

**Symptoms:**
```
Error posting message to Mastodon: 401 Unauthorized
```

**Diagnosis:**

1. **Test access token:**
```bash
curl -H "Authorization: Bearer $MASTO_ACCESS_TOKEN" \
  ${MASTO_BASEURL}/api/v1/accounts/verify_credentials

# Expected: {"id":"123","username":"youruser",...}
# Error: {"error":"The access token is invalid"}
```

2. **Check token scope:**
```bash
# Token must have 'write:statuses' scope
curl -H "Authorization: Bearer $MASTO_ACCESS_TOKEN" \
  ${MASTO_BASEURL}/api/v1/apps/verify_credentials

# Check "scopes" field in response
```

**Solutions:**

- **Token expired:** Regenerate token in Mastodon Settings → Development
- **Insufficient scope:** Create new application with `write:statuses` scope
- **Wrong instance:** Verify `MASTO_BASEURL` matches token's instance

---

### Problem: Messages Not Appearing in Timeline

**Symptoms:**
- No errors in logs
- `To Telegram...done.` and `To Mastodon...done.` printed
- Messages not visible in channel/timeline

**Diagnosis:**

1. **Check message visibility:**
```bash
# Telegram: Verify channel is public and bot has 'post_messages' permission
# Mastodon: Check toot visibility setting (should be 'public')

# Test visibility manually
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${TELEGRAM_CHANNEL_ID}" \
  -d "text=Manual test message"
```

2. **Check rate limits:**
```bash
# Telegram: Max 30 messages/second per bot
# Mastodon: Max 300 requests per 5 minutes

# Check for rate limit errors in logs
grep -i "rate limit\|too many requests" /var/log/rocketalert.log
```

**Solutions:**

- **Telegram silent mode:** Ensure `disable_notification=False` (current code doesn't set this, defaults to False)
- **Mastodon private toots:** Verify visibility is `public` (default in code)
- **Rate limited:** Add delay between messages: `time.sleep(0.5)`

---

### Problem: Message Truncation Bug (Mastodon)

**Symptoms:**
- Long messages missing content in Mastodon
- Telegram messages complete

**Diagnosis:**

This is a **known bug** in `mastodon_bot.py:52`:

```python
# Bug: Should start new message with current line
else:
    truncatedMessages.append(newMessage)
    newMessage = ""  # BUG: Loses current line!
```

**Temporary Solution:**

```python
# Quick patch (edit mastodon_bot.py:52)
else:
    if newMessage:
        truncatedMessages.append(newMessage)
    newMessage = f"{line}\n"  # Fix: Keep current line
```

**Permanent Solution:**

Apply patch and run tests:
```bash
# Edit file
vim mastodon_bot.py

# Run tests to verify fix
pytest tests/unit/test_mastodon_bot.py -v

# Commit fix
git add mastodon_bot.py
git commit -m "Fix Mastodon truncation bug: preserve lines exceeding limit"
```

---

## Performance Problems

### Problem: High Latency (Slow Event Processing)

**Symptoms:**
```
2025-12-30 14:30:00 - Received server event: {...}
2025-12-30 14:30:05 - Event process completed.  # 5 seconds!
```

**Diagnosis:**

1. **Profile execution time:**
```python
# Add timing to message_manager.py
import time

def postMessage(self, eventData):
    start = time.time()

    # ... existing code ...

    telegram_start = time.time()
    self.telegramBot.sendMessage(text)
    print(f"Telegram: {time.time() - telegram_start:.2f}s")

    mastodon_start = time.time()
    self.mastodonBot.sendMessage(text)
    print(f"Mastodon: {time.time() - mastodon_start:.2f}s")

    print(f"Total: {time.time() - start:.2f}s")
```

2. **Check API latency:**
```bash
# Telegram API ping
time curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe" > /dev/null

# Mastodon API ping
time curl -s "${MASTO_BASEURL}/api/v1/instance" > /dev/null
```

**Solutions:**

| Bottleneck | Fix |
|------------|-----|
| Slow Telegram API | Retry with backoff, consider alternative bot library |
| Slow Mastodon instance | Increase timeout, use faster instance, or self-host |
| Network latency | Deploy closer to API servers (cloud region) |
| CPU bound | Enable async I/O (requires code refactor) |

**Optimization: Async Bot Posting (Future Enhancement)**

```python
# Replace sequential posting with concurrent
import asyncio

async def post_message_async(telegram_bot, mastodon_bot, text):
    await asyncio.gather(
        telegram_bot.send_message_async(text),
        mastodon_bot.send_message_async(text)
    )
    # Reduces latency by ~50% (200ms Telegram + 500ms Mastodon = 700ms → 500ms max)
```

---

### Problem: High Memory Usage

**Symptoms:**
```
# Kubernetes: Pod OOMKilled
kubectl get pods -n bots
# NAME                                READY   STATUS      RESTARTS
# rocketalert-bots-abc123-xyz         0/1     OOMKilled   5
```

**Diagnosis:**

1. **Check memory usage:**
```bash
# Docker
docker stats rocketalert-bots

# Kubernetes
kubectl top pod -n bots -l app=rocketalert-bots

# Inside container
free -m
ps aux --sort=-%mem | head
```

2. **Profile memory:**
```python
# Add to main.py
import tracemalloc

tracemalloc.start()

# ... after processing event ...
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
print("[ Top 10 memory consumers ]")
for stat in top_stats[:10]:
    print(stat)
```

**Solutions:**

- **Large JSON events:** Limit alerts processed per event (chunk batches)
- **Memory leak:** Update dependencies, check for circular references
- **polygons.json loaded:** Comment out loading (line 16-20 in message_builder.py) if unused
- **Increase limits:** Update Kubernetes resource limits

```yaml
resources:
  limits:
    memory: "512Mi"  # Increase from 256Mi
```

---

### Problem: CPU Throttling (Kubernetes)

**Symptoms:**
```
# High CPU usage, slow processing
kubectl top pod -n bots -l app=rocketalert-bots
# NAME                          CPU    MEMORY
# rocketalert-bots-abc123-xyz   500m   120Mi  # At limit!
```

**Diagnosis:**

```bash
# Check CPU throttling
kubectl describe pod -n bots -l app=rocketalert-bots | grep -A 5 "Limits"

# Inside pod
cat /sys/fs/cgroup/cpu/cpu.stat
# Look for "nr_throttled" and "throttled_time"
```

**Solutions:**

```yaml
# Increase CPU limits
resources:
  requests:
    cpu: "200m"
  limits:
    cpu: "1000m"  # Allow bursts up to 1 core
```

---

## Deployment Issues

### Problem: Kubernetes Pod CrashLoopBackOff

**Symptoms:**
```
kubectl get pods -n bots
# NAME                                READY   STATUS             RESTARTS
# rocketalert-bots-abc123-xyz         0/1     CrashLoopBackOff   8
```

**Diagnosis:**

1. **Check pod logs:**
```bash
kubectl logs -n bots -l app=rocketalert-bots --tail=100

# Check previous pod instance
kubectl logs -n bots -l app=rocketalert-bots --previous
```

2. **Check pod events:**
```bash
kubectl describe pod -n bots -l app=rocketalert-bots | grep -A 20 Events
```

3. **Check exit code:**
```bash
kubectl get pod -n bots -l app=rocketalert-bots -o jsonpath='{.status.containerStatuses[0].lastState.terminated.exitCode}'
# 1 = Initialization failure (e.g., missing env var)
# 137 = OOMKilled
# 143 = SIGTERM (graceful shutdown)
```

**Solutions:**

| Exit Code | Cause | Fix |
|-----------|-------|-----|
| 1 | Missing env var | Check secret exists and is mounted |
| 137 | Out of memory | Increase memory limits |
| 143 | Killed by signal | Check liveness probe configuration |

**Quick Fix:**
```bash
# Delete pod to force restart
kubectl delete pod -n bots -l app=rocketalert-bots

# If still failing, check secrets
kubectl get secret rocketalert-secrets -n bots -o yaml | grep -v "data:"
```

---

### Problem: Docker Image Pull Failed

**Symptoms:**
```
kubectl describe pod -n bots -l app=rocketalert-bots
# Events:
#   Failed to pull image "ghcr.io/aserper/rocketalert-bots:latest": rpc error: code = Unknown desc = Error response from daemon: pull access denied
```

**Diagnosis:**

1. **Test image pull locally:**
```bash
docker pull ghcr.io/aserper/rocketalert-bots:latest
# Error: Error response from daemon: pull access denied, repository does not exist or may require 'docker login'
```

2. **Verify image exists:**
```bash
# Check Docker Hub
curl -s https://hub.docker.com/v2/repositories/amitserper/rocketalert-mastodon/tags | jq .

# Check GHCR (requires auth)
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://ghcr.io/v2/aserper/rocketalert-bots/tags/list
```

**Solutions:**

- **Private GHCR image:** Create pull secret
```bash
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=aserper \
  --docker-password=$GITHUB_TOKEN \
  --namespace=bots

# Verify secret in deployment.yaml
spec:
  imagePullSecrets:
  - name: ghcr-secret
```

- **Image doesn't exist:** Build and push image
```bash
docker build -t ghcr.io/aserper/rocketalert-bots:latest .
docker push ghcr.io/aserper/rocketalert-bots:latest
```

- **Use public Docker Hub image:**
```yaml
spec:
  containers:
  - name: rocketalert-bots
    image: amitserper/rocketalert-mastodon:latest  # Public image
```

---

### Problem: Liveness Probe Failing

**Symptoms:**
```
kubectl describe pod -n bots -l app=rocketalert-bots
# Events:
#   Liveness probe failed: /bin/sh: 1: [: Illegal number:
#   Container will be restarted
```

**Diagnosis:**

1. **Test probe manually:**
```bash
kubectl exec -it -n bots deployment/rocketalert-bots -- /bin/sh -c '
  if [ ! -f /tmp/heartbeat ]; then exit 1; fi
  LAST=$(cat /tmp/heartbeat)
  NOW=$(date +%s)
  DIFF=$((NOW - ${LAST%.*}))
  echo "Heartbeat age: ${DIFF}s"
  if [ $DIFF -gt 90 ]; then exit 1; fi
  exit 0
'
```

2. **Check heartbeat file format:**
```bash
kubectl exec -it -n bots deployment/rocketalert-bots -- cat /tmp/heartbeat
# Should be Unix timestamp: 1735587845.123456
```

**Solutions:**

- **Heartbeat file missing:** Process not receiving KEEP_ALIVE events (check API connection)
- **Heartbeat stale:** Process stuck (check logs for errors, restart pod)
- **Probe script error:** Fix shell script in deployment YAML (ensure proper quoting)

---

## Debug Logging

### Enable Verbose Logging

**Method 1: Environment Variable (Future Enhancement)**

```bash
# Add to deployment
env:
- name: LOG_LEVEL
  value: "DEBUG"

# Update main.py to read LOG_LEVEL
import os
import logging

log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=getattr(logging, log_level))
```

**Method 2: Temporary Code Change**

```python
# Add to top of main.py
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Replace print() statements with logging
logger = logging.getLogger(__name__)
logger.info(f"Starting version: {commit_sha}")
logger.debug(f"Connecting to {api.baseURL}")
```

### Structured Logging (Recommended for Production)

```python
# Add structured logging library
# pip install structlog

import structlog

logger = structlog.get_logger()

# Log with context
logger.info("event_received",
            alert_type_id=eventData["alertTypeId"],
            alert_count=len(eventData["alerts"]))

# Output (JSON):
# {"event": "event_received", "alert_type_id": 1, "alert_count": 5, "timestamp": "2025-12-30T14:30:00Z"}
```

### Log Levels

| Level | Usage | Example |
|-------|-------|---------|
| DEBUG | Detailed diagnostic info | `DEBUG: Connecting to https://...` |
| INFO | General informational messages | `Event process completed.` |
| WARNING | Warning messages (recoverable errors) | `Telegram post failed, retrying...` |
| ERROR | Error messages (handled exceptions) | `Error posting message to Telegram: ...` |
| CRITICAL | Critical errors (unrecoverable) | `CRITICAL ERROR: Failed to connect to Telegram` |

---

## Log Analysis

### Common Log Patterns

**Normal Operation:**
```
2025-12-30 14:30:00 - Starting version: abc123def456 - Connecting to server...
DEBUG: Calling listenToServerEvents...
DEBUG: Connection established. Listening for events...
2025-12-30 14:30:20 - Received server event: {"alertTypeId":0,"alerts":[{"name":"KEEP_ALIVE",...}]}
2025-12-30 14:30:20 - DEBUG: Received Keep alive
2025-12-30 14:30:45 - Received server event: {"alertTypeId":1,"alerts":[{...}]}
2025-12-30 14:30:45 - Processing event...
Building alert message...
  Posting:
    Message 1/1:
      To Telegram...done.
      To Mastodon...done.
2025-12-30 14:30:46 - Event process completed.
```

**Connection Issues:**
```
Connection error: HTTPSConnectionPool(host='ra-agg.kipodopik.com', port=443): Max retries exceeded
# → Network/firewall issue, check connectivity

Connection timeout (no data received in 60s), reconnecting...
# → No keep-alive events, check API status

Error decoding JSON: Expecting value: line 1 column 1 (char 0)
# → Malformed SSE data, skip and continue
```

**Bot Errors:**
```
Error posting message to Telegram: Unauthorized
# → Invalid bot token, regenerate

Error posting message to Mastodon: 401 Client Error
# → Invalid access token, regenerate

Error posting message to Telegram: Chat not found
# → Bot not admin of channel, add bot and promote
```

### Log Aggregation (Kubernetes)

**Using kubectl:**
```bash
# Stream logs
kubectl logs -f -n bots deployment/rocketalert-bots

# Last N lines
kubectl logs --tail=200 -n bots deployment/rocketalert-bots

# Since timestamp
kubectl logs --since-time="2025-12-30T14:00:00Z" -n bots deployment/rocketalert-bots

# Grep for errors
kubectl logs -n bots deployment/rocketalert-bots | grep -i "error\|critical\|failed"
```

**Using Fluentd/Fluent Bit:**

```yaml
# fluentd-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: kube-system
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/rocketalert-bots*.log
      pos_file /var/log/rocketalert-bots.log.pos
      tag rocketalert.*
      <parse>
        @type json
      </parse>
    </source>

    <match rocketalert.**>
      @type elasticsearch
      host elasticsearch.logging.svc.cluster.local
      port 9200
      index_name rocketalert
    </match>
```

**Using Grafana Loki:**

```yaml
# promtail-config.yaml
scrape_configs:
- job_name: kubernetes-pods
  kubernetes_sd_configs:
  - role: pod
    namespaces:
      names:
      - bots
  relabel_configs:
  - source_labels: [__meta_kubernetes_pod_label_app]
    action: keep
    regex: rocketalert-bots
```

### Metrics & Monitoring

**Prometheus Metrics (Future Enhancement):**

```python
# Add to main.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Metrics
events_received = Counter('rocketalert_events_total', 'Total events received', ['alert_type'])
alerts_processed = Counter('rocketalert_alerts_total', 'Total alerts processed')
processing_duration = Histogram('rocketalert_processing_seconds', 'Event processing duration')
telegram_errors = Counter('rocketalert_telegram_errors_total', 'Telegram posting errors')
mastodon_errors = Counter('rocketalert_mastodon_errors_total', 'Mastodon posting errors')
heartbeat_age = Gauge('rocketalert_heartbeat_age_seconds', 'Age of last heartbeat')

# Instrument code
start_http_server(8000)  # Expose metrics on :8000/metrics

events_received.labels(alert_type=eventData['alertTypeId']).inc()
with processing_duration.time():
    messageManager.postMessage(eventData)
```

**Grafana Dashboard Queries:**

```promql
# Event rate
rate(rocketalert_events_total[5m])

# Average processing time
rate(rocketalert_processing_seconds_sum[5m]) / rate(rocketalert_processing_seconds_count[5m])

# Error rate
rate(rocketalert_telegram_errors_total[5m]) + rate(rocketalert_mastodon_errors_total[5m])

# Heartbeat staleness alert
rocketalert_heartbeat_age_seconds > 90
```

---

## Common Error Messages

### Connection Errors

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `Max retries exceeded with url` | Network/DNS failure | Check connectivity, DNS, firewall rules |
| `Connection timeout (no data received in 60s)` | No keep-alive events | Verify API status, increase timeout |
| `Connection refused` | Port blocked | Check firewall, verify port 443 open |
| `SSL: CERTIFICATE_VERIFY_FAILED` | Invalid/expired cert | Update CA certificates, verify API cert |
| `Name or service not known` | DNS resolution failed | Check DNS servers, verify hostname |

### Authentication Errors

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `CRITICAL ERROR: TELEGRAM_BOT_TOKEN environment variable not set` | Missing env var | Set `TELEGRAM_BOT_TOKEN` in environment |
| `Unauthorized` (Telegram) | Invalid bot token | Regenerate token via @BotFather |
| `401 Unauthorized` (Mastodon) | Invalid access token | Regenerate token in Mastodon settings |
| `403 Forbidden` (Telegram) | Bot not channel admin | Add bot to channel, promote to admin |
| `Chat not found` | Invalid channel ID | Verify `TELEGRAM_CHANNEL_ID` is correct |

### Processing Errors

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `Error decoding JSON: Expecting value` | Malformed SSE data | Skip event, check API logs |
| `KeyError: 'alerts'` | Invalid event structure | Add error handling, validate event schema |
| `TypeError: 'NoneType' object is not iterable` | Null alert data | Add null checks before iteration |
| `UnicodeDecodeError` | Encoding issue | Ensure `response.encoding = 'utf-8'` |

### Deployment Errors

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `CrashLoopBackOff` | Startup failure | Check logs, verify env vars, secrets |
| `ImagePullBackOff` | Cannot pull image | Verify image exists, check pull secret |
| `OOMKilled` | Out of memory | Increase memory limits |
| `Liveness probe failed` | Heartbeat stale | Check process status, SSE connection |

---

## Advanced Debugging

### Interactive Debugging (Local)

**Using pdb (Python Debugger):**

```python
# Add breakpoint in main.py
import pdb

def main():
    # ... existing code ...
    for line in response.iter_lines(decode_unicode=True):
        pdb.set_trace()  # Pause execution
        line = line.lstrip("data:")
        # ... continue ...
```

**Run with debugger:**
```bash
python -m pdb main.py

# Commands:
# n - next line
# s - step into function
# c - continue
# p variable - print variable
# q - quit
```

### Remote Debugging (Kubernetes)

**Using debugpy:**

```python
# Add to main.py
import debugpy
debugpy.listen(("0.0.0.0", 5678))
print("Waiting for debugger attach...")
debugpy.wait_for_client()
```

**Port forward and attach:**
```bash
# Port forward
kubectl port-forward -n bots deployment/rocketalert-bots 5678:5678

# Attach VS Code debugger (launch.json)
{
  "name": "Python: Remote Attach",
  "type": "python",
  "request": "attach",
  "connect": {
    "host": "localhost",
    "port": 5678
  },
  "pathMappings": [
    {
      "localRoot": "${workspaceFolder}",
      "remoteRoot": "/app"
    }
  ]
}
```

### Packet Capture (Network Analysis)

**Capture SSE stream:**
```bash
# tcpdump
sudo tcpdump -i any -s 0 -w rocketalert.pcap host ra-agg.kipodopik.com

# Kubernetes
kubectl debug -it -n bots deployment/rocketalert-bots --image=nicolaka/netshoot
tcpdump -i eth0 -s 0 -w /tmp/capture.pcap host ra-agg.kipodopik.com
```

**Analyze with Wireshark:**
```bash
wireshark rocketalert.pcap
# Filter: tcp.port == 443 && http
# Look for SSE data stream
```

### Core Dump Analysis

**Enable core dumps:**
```bash
# Set ulimit
ulimit -c unlimited

# Run with faulthandler
python -X faulthandler main.py

# Core dump location
ls -lh /var/crash/ /tmp/core*
```

**Analyze core dump:**
```bash
gdb python core.<pid>
(gdb) bt  # Backtrace
(gdb) info threads
(gdb) py-bt  # Python backtrace
```

### Heap Profiling (Memory Leaks)

**Using memory_profiler:**
```python
# Install: pip install memory_profiler

from memory_profiler import profile

@profile
def postMessage(self, eventData):
    # ... existing code ...
```

**Run:**
```bash
python -m memory_profiler main.py
# Output shows line-by-line memory usage
```

---

## Appendix

### Diagnostic Commands Cheat Sheet

```bash
# === Local Testing ===
# Test environment variables
env | grep -E "RA_|TELEGRAM_|MASTO_|MAPBOX_"

# Test bot connections
python -c "from telegram_bot import TelegramBot; TelegramBot()"
python -c "from mastodon_bot import MastodonBot; MastodonBot()"

# Test API connection
curl -N https://ra-agg.kipodopik.com/api/v2/alerts/real-time?alertTypeId=-1 \
  -H "X-SECURITY-TOKEN: $CUSTOM_HEADER_VALUE" \
  -H "user-agent: Mozilla/5.0 ..."

# === Docker ===
# View logs
docker logs -f rocketalert-bots

# Exec into container
docker exec -it rocketalert-bots /bin/sh

# Container stats
docker stats rocketalert-bots

# === Kubernetes ===
# Check pod status
kubectl get pods -n bots -l app=rocketalert-bots

# View logs
kubectl logs -f -n bots deployment/rocketalert-bots

# Describe pod (events)
kubectl describe pod -n bots -l app=rocketalert-bots

# Exec into pod
kubectl exec -it -n bots deployment/rocketalert-bots -- /bin/sh

# Port forward (debugging)
kubectl port-forward -n bots deployment/rocketalert-bots 8000:8000

# Resource usage
kubectl top pod -n bots -l app=rocketalert-bots

# === Network ===
# Test connectivity
ping ra-agg.kipodopik.com
telnet ra-agg.kipodopik.com 443
curl -v https://ra-agg.kipodopik.com

# DNS lookup
nslookup ra-agg.kipodopik.com
dig ra-agg.kipodopik.com

# Trace route
traceroute ra-agg.kipodopik.com
```

### External Resources

- [Telegram Bot API Docs](https://core.telegram.org/bots/api)
- [Mastodon API Docs](https://docs.joinmastodon.org/api/)
- [Python Requests Docs](https://requests.readthedocs.io/)
- [Kubernetes Debugging Guide](https://kubernetes.io/docs/tasks/debug/)
- [Docker Logging Best Practices](https://docs.docker.com/config/containers/logging/)

### Document Version

- **Version:** 1.0
- **Last Updated:** 2025-12-30
- **Author:** Troubleshooting Guide
