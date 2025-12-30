# RocketAlert Bots - Setup & Deployment Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Local Development Setup](#local-development-setup)
4. [Running Locally](#running-locally)
5. [Testing](#testing)
6. [Docker Build & Run](#docker-build--run)
7. [Kubernetes Deployment](#kubernetes-deployment)
8. [ArgoCD GitOps Deployment](#argocd-gitops-deployment)
9. [Configuration Management](#configuration-management)
10. [Health Checks & Monitoring](#health-checks--monitoring)
11. [Maintenance & Operations](#maintenance--operations)

---

## Overview

This guide provides step-by-step instructions for setting up the RocketAlert Bots system in various environments:

- **Local Development** - Run on your workstation for testing
- **Docker** - Containerized deployment for portability
- **Kubernetes** - Production deployment with orchestration
- **ArgoCD** - GitOps-based continuous deployment

**Deployment Options Comparison:**

| Method | Use Case | Complexity | Scalability | Production-Ready |
|--------|----------|------------|-------------|------------------|
| Local Python | Development/debugging | Low | N/A | ❌ No |
| Docker | Testing/staging | Medium | Single instance | ⚠️ Partial |
| Kubernetes | Production | High | High availability | ✅ Yes |
| ArgoCD | Production GitOps | High | Automated CD | ✅ Yes |

---

## Prerequisites

### System Requirements

**Hardware:**
- CPU: 1 core minimum, 2 cores recommended
- RAM: 256MB minimum, 512MB recommended
- Storage: 500MB for dependencies + container images
- Network: Stable internet connection (SSE stream)

**Operating System:**
- Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+)
- macOS 12+ (Intel or Apple Silicon)
- Windows 10+ with WSL2 (for Docker/Kubernetes)

### Software Dependencies

**Required:**
- Python 3.10 or higher
- pip (Python package manager)
- Git (version control)

**Optional (for Docker/Kubernetes):**
- Docker 20.10+ or Podman 3.0+
- kubectl 1.24+ (Kubernetes CLI)
- ArgoCD CLI (for GitOps deployment)

### Account Setup

**1. Telegram Bot Token**

Create a bot via [@BotFather](https://t.me/botfather):

```
Step 1: Message @BotFather on Telegram
Step 2: Send command: /newbot
Step 3: Choose bot name (e.g., "RocketAlert Bot")
Step 4: Choose username (e.g., "rocketalert_bot")
Step 5: Copy token: 8271024720:AAFrkR15ixUljp4nDVWLaLVZKFLZDBazd8I
Step 6: Add bot as admin to target channel (e.g., @RocketAlert)
```

**2. Mastodon Access Token**

Generate token from Mastodon instance:

```
Step 1: Log into https://mastodon.social (or your instance)
Step 2: Settings → Development → New Application
Step 3: Application name: "RocketAlert Bots"
Step 4: Scopes: Select "write:statuses" only
Step 5: Submit → Copy "Your access token"
Step 6: Save token: x1C8wV94MO5vCbdjEE6CjdifprKVydPNYbzFFK0TCFI
```

**3. RocketAlert API Access**

Contact RocketAlert API provider for:
- Base URL (e.g., `https://ra-agg.kipodopik.com/api/v2/alerts`)
- Custom header key (e.g., `X-SECURITY-TOKEN`)
- Custom header value (secret authentication token)

---

## Local Development Setup

### Step 1: Clone Repository

```bash
# Clone via HTTPS
git clone https://github.com/aserper/rocketalert-bots.git
cd rocketalert-bots

# Or clone via SSH (requires SSH key setup)
git clone git@github.com:aserper/rocketalert-bots.git
cd rocketalert-bots
```

**Verify Repository:**
```bash
git log --oneline -5
# Should show recent commits
```

### Step 2: Create Virtual Environment

**Option A: venv (Standard Library)**
```bash
# Create virtual environment
python3 -m venv .venv

# Activate (Linux/macOS)
source .venv/bin/activate

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Verify activation
which python  # Should show .venv/bin/python
python --version  # Should be 3.10+
```

**Option B: virtualenv (Third-Party)**
```bash
# Install virtualenv
pip install virtualenv

# Create environment
virtualenv .venv

# Activate (same as venv above)
source .venv/bin/activate
```

### Step 3: Install Dependencies

**Production Dependencies:**
```bash
# Install from requirements.txt
pip install -r requirements.txt

# Verify installation
pip list | grep -E '(requests|pytelegrambotapi|mastodon)'
# Should show:
# requests        2.32.5
# pyTelegramBotAPI 4.14.0
# mastodon-py     2.1.4
```

**Development Dependencies (Optional):**
```bash
# Includes pytest, coverage, etc.
pip install -r requirements.txt
# (All dependencies in single file)
```

### Step 4: Configure Environment Variables

**Option A: .env File (Recommended)**
```bash
# Create .env file
cat > .env << 'EOF'
# RocketAlert API
RA_BASEURL=https://ra-agg.kipodopik.com/api/v2/alerts
CUSTOM_HEADER_KEY=X-SECURITY-TOKEN
CUSTOM_HEADER_VALUE=your_secret_token_here

# Telegram
TELEGRAM_BOT_TOKEN=8271024720:AAFrkR15ixUljp4nDVWLaLVZKFLZDBazd8I
TELEGRAM_CHANNEL_ID=@RocketAlert

# Mastodon
MASTO_BASEURL=https://mastodon.social
MASTO_ACCESS_TOKEN=x1C8wV94MO5vCbdjEE6CjdifprKVydPNYbzFFK0TCFI

# Mapbox (required but unused)
MAPBOX_TOKEN=pk.eyJ1IjoiZXJlem5hZ2FyIiwiYSI6ImNsb2pmcXV4ZzFreXgyam8zdjdvdWtqMHMifQ.e2E4pq7dQZL7_YszHD25kA
EOF

# Load environment variables
export $(grep -v '^#' .env | xargs)
```

**Option B: Shell Exports**
```bash
export RA_BASEURL="https://ra-agg.kipodopik.com/api/v2/alerts"
export CUSTOM_HEADER_KEY="X-SECURITY-TOKEN"
export CUSTOM_HEADER_VALUE="your_secret_token_here"
export TELEGRAM_BOT_TOKEN="8271024720:AAFrkR15ix..."
export TELEGRAM_CHANNEL_ID="@RocketAlert"
export MASTO_BASEURL="https://mastodon.social"
export MASTO_ACCESS_TOKEN="x1C8wV94MO5vCbdjEE6C..."
export MAPBOX_TOKEN="pk.eyJ1..."
```

**Verify Configuration:**
```bash
python -c "import os; print('RA_BASEURL:', os.getenv('RA_BASEURL'))"
# Should print: RA_BASEURL: https://ra-agg.kipodopik.com/api/v2/alerts
```

### Step 5: Verify Setup

**Test Dependencies:**
```bash
python -c "import requests, telebot, mastodon; print('All imports successful')"
# Should print: All imports successful
```

**Test Bot Connections:**
```bash
# Test Telegram bot (quick validation)
python -c "
import os
from telebot import TeleBot
bot = TeleBot(os.environ['TELEGRAM_BOT_TOKEN'])
info = bot.get_me()
print(f'Connected to Telegram as @{info.username}')
"
# Should print: Connected to Telegram as @your_bot_username

# Test Mastodon connection
python -c "
import os
from mastodon import Mastodon
m = Mastodon(
    api_base_url=os.environ['MASTO_BASEURL'],
    access_token=os.environ['MASTO_ACCESS_TOKEN']
)
print(f'Connected to Mastodon at {os.environ[\"MASTO_BASEURL\"]}')
"
# Should print: Connected to Mastodon at https://mastodon.social
```

---

## Running Locally

### Standard Execution

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Run application
python main.py
```

**Expected Output:**
```
DEBUG: Initializing MessageManager...
DEBUG: Initializing TelegramBot...
DEBUG: Connected as @rocketalert_bot
DEBUG: Initializing MastodonBot...
DEBUG: MessageManager initialized.
2025-12-30 14:30:15 - Starting version: unknown - Connecting to server and starting listening to events...
DEBUG: Calling listenToServerEvents...
DEBUG: Connecting to https://ra-agg.kipodopik.com/api/v2/alerts/real-time?alertTypeId=-1...
DEBUG: Request Headers: {'X-SECURITY-TOKEN': '***REDACTED***', 'user-agent': 'Mozilla/5.0 ...'}
DEBUG: Connection established. Listening for events...
2025-12-30 14:30:45 - Received server event: {"alertTypeId":0,"alerts":[{"name":"KEEP_ALIVE",...}]}
2025-12-30 14:30:45 - DEBUG: Received Keep alive
```

### Background Execution

**Using nohup (Linux/macOS):**
```bash
nohup python main.py > rocketalert.log 2>&1 &
echo $! > rocketalert.pid

# Monitor logs
tail -f rocketalert.log

# Stop process
kill $(cat rocketalert.pid)
```

**Using screen:**
```bash
# Start screen session
screen -S rocketalert

# Run application
python main.py

# Detach: Ctrl+A, then D

# Reattach
screen -r rocketalert

# Kill session
screen -X -S rocketalert quit
```

**Using systemd (Linux):**
```bash
# Create service file
sudo tee /etc/systemd/system/rocketalert.service << 'EOF'
[Unit]
Description=RocketAlert Bots
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/rocketalert-bots
Environment="RA_BASEURL=https://..."
Environment="CUSTOM_HEADER_KEY=X-SECURITY-TOKEN"
Environment="CUSTOM_HEADER_VALUE=secret"
Environment="TELEGRAM_BOT_TOKEN=123456:ABC..."
Environment="TELEGRAM_CHANNEL_ID=@RocketAlert"
Environment="MASTO_BASEURL=https://mastodon.social"
Environment="MASTO_ACCESS_TOKEN=token"
Environment="MAPBOX_TOKEN=pk.mapbox_token"
ExecStart=/home/youruser/rocketalert-bots/.venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Start service
sudo systemctl start rocketalert

# Enable on boot
sudo systemctl enable rocketalert

# View logs
sudo journalctl -u rocketalert -f
```

### Debugging Mode

**Enable Fault Handler:**
```bash
# Already enabled in main.py (line 24)
# To trigger traceback dump:
kill -USR1 <pid>

# View traceback in logs
```

**Verbose Logging:**
```python
# Add to main.py (temporary debugging)
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Testing

### Run All Tests

```bash
# Basic test run
pytest

# Verbose output
pytest -v

# With coverage report
pytest --cov=. --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

**Expected Output:**
```
========================= test session starts ==========================
platform linux -- Python 3.10.12, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/amit/projects/rocketalert-bots
configfile: pytest.ini
plugins: asyncio-1.3.0, cov-7.0.0, mock-3.15.1
collected 60 items

tests/unit/test_message_builder.py ............. [ 21%]
tests/unit/test_telegram_bot.py ............ [ 41%]
tests/unit/test_mastodon_bot.py ............ [ 61%]
tests/unit/test_message_manager.py ........ [ 74%]
tests/unit/test_rocket_alert_api.py ......... [ 89%]
tests/integration/test_end_to_end.py ....... [100%]

---------- coverage: platform linux, python 3.10.12 -----------
Name                        Stmts   Miss  Cover
-----------------------------------------------
mastodon_bot.py                20      0   100%
message_builder.py             37      7    79%
message_manager.py             25      1    97%
rocket_alert_api.py            10      0   100%
telegram_bot.py                36      7    81%
main.py                        45     45     0%
-----------------------------------------------
TOTAL                         173     60    71%

========================= 60 passed in 2.34s ===========================
```

### Run Specific Test Suites

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific module tests
pytest tests/unit/test_telegram_bot.py -v

# Specific test
pytest tests/unit/test_telegram_bot.py::TestTelegramBot::test_sendMessage_short -v
```

### Test with Different Python Versions

**Using tox (if configured):**
```bash
# Install tox
pip install tox

# Run tests on multiple Python versions
tox
```

**Manual testing:**
```bash
# Python 3.10
python3.10 -m pytest

# Python 3.11
python3.11 -m pytest

# Python 3.12
python3.12 -m pytest
```

### Continuous Testing (Watch Mode)

```bash
# Install pytest-watch
pip install pytest-watch

# Run tests on file change
ptw -- -v
```

---

## Docker Build & Run

### Build Docker Image

**Standard Build:**
```bash
# Build with commit SHA
docker build \
  --build-arg COMMIT_SHA=$(git rev-parse HEAD) \
  -t rocketalert-bots:latest \
  .

# Verify image
docker images rocketalert-bots
```

**Multi-Platform Build (for ARM + AMD):**
```bash
# Set up buildx (one-time)
docker buildx create --name multiarch --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --build-arg COMMIT_SHA=$(git rev-parse HEAD) \
  -t rocketalert-bots:latest \
  --push \
  .
```

**Build with Custom Tag:**
```bash
# Version tag
docker build \
  --build-arg COMMIT_SHA=$(git rev-parse HEAD) \
  -t rocketalert-bots:v2.0.0 \
  .

# Latest + version tags
docker build \
  --build-arg COMMIT_SHA=$(git rev-parse HEAD) \
  -t rocketalert-bots:latest \
  -t rocketalert-bots:v2.0.0 \
  .
```

### Run Docker Container

**Interactive Mode (for testing):**
```bash
docker run -it --rm \
  -e RA_BASEURL="https://ra-agg.kipodopik.com/api/v2/alerts" \
  -e CUSTOM_HEADER_KEY="X-SECURITY-TOKEN" \
  -e CUSTOM_HEADER_VALUE="your_secret_token" \
  -e TELEGRAM_BOT_TOKEN="8271024720:AAFrkR15ix..." \
  -e TELEGRAM_CHANNEL_ID="@RocketAlert" \
  -e MASTO_BASEURL="https://mastodon.social" \
  -e MASTO_ACCESS_TOKEN="x1C8wV94MO5vCbdjEE6C..." \
  -e MAPBOX_TOKEN="pk.eyJ1..." \
  rocketalert-bots:latest
```

**Detached Mode (production):**
```bash
docker run -d \
  --name rocketalert-bots \
  --restart unless-stopped \
  -e RA_BASEURL="https://ra-agg.kipodopik.com/api/v2/alerts" \
  -e CUSTOM_HEADER_KEY="X-SECURITY-TOKEN" \
  -e CUSTOM_HEADER_VALUE="your_secret_token" \
  -e TELEGRAM_BOT_TOKEN="8271024720:AAFrkR15ix..." \
  -e TELEGRAM_CHANNEL_ID="@RocketAlert" \
  -e MASTO_BASEURL="https://mastodon.social" \
  -e MASTO_ACCESS_TOKEN="x1C8wV94MO5vCbdjEE6C..." \
  -e MAPBOX_TOKEN="pk.eyJ1..." \
  rocketalert-bots:latest

# View logs
docker logs -f rocketalert-bots

# Stop container
docker stop rocketalert-bots

# Remove container
docker rm rocketalert-bots
```

**Using Environment File:**
```bash
# Create .env.docker file
cat > .env.docker << 'EOF'
RA_BASEURL=https://ra-agg.kipodopik.com/api/v2/alerts
CUSTOM_HEADER_KEY=X-SECURITY-TOKEN
CUSTOM_HEADER_VALUE=your_secret_token
TELEGRAM_BOT_TOKEN=8271024720:AAFrkR15ix...
TELEGRAM_CHANNEL_ID=@RocketAlert
MASTO_BASEURL=https://mastodon.social
MASTO_ACCESS_TOKEN=x1C8wV94MO5vCbdjEE6C...
MAPBOX_TOKEN=pk.eyJ1...
EOF

# Run with env file
docker run -d \
  --name rocketalert-bots \
  --env-file .env.docker \
  --restart unless-stopped \
  rocketalert-bots:latest
```

### Docker Compose (Optional)

```yaml
# docker-compose.yml
version: '3.8'

services:
  rocketalert-bots:
    build:
      context: .
      args:
        COMMIT_SHA: ${COMMIT_SHA:-unknown}
    image: rocketalert-bots:latest
    container_name: rocketalert-bots
    restart: unless-stopped
    environment:
      - TZ=America/New_York
      - RA_BASEURL=${RA_BASEURL}
      - CUSTOM_HEADER_KEY=${CUSTOM_HEADER_KEY}
      - CUSTOM_HEADER_VALUE=${CUSTOM_HEADER_VALUE}
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_CHANNEL_ID=${TELEGRAM_CHANNEL_ID}
      - MASTO_BASEURL=${MASTO_BASEURL}
      - MASTO_ACCESS_TOKEN=${MASTO_ACCESS_TOKEN}
      - MAPBOX_TOKEN=${MAPBOX_TOKEN}
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**Usage:**
```bash
# Start service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop service
docker-compose down
```

### Push to Registry

**Docker Hub:**
```bash
# Login
docker login -u amitserper

# Tag image
docker tag rocketalert-bots:latest amitserper/rocketalert-mastodon:latest

# Push
docker push amitserper/rocketalert-mastodon:latest
```

**GitHub Container Registry:**
```bash
# Login
echo $GITHUB_TOKEN | docker login ghcr.io -u aserper --password-stdin

# Tag image
docker tag rocketalert-bots:latest ghcr.io/aserper/rocketalert-bots:latest
docker tag rocketalert-bots:latest ghcr.io/aserper/rocketalert-bots:$(git rev-parse HEAD)

# Push
docker push ghcr.io/aserper/rocketalert-bots:latest
docker push ghcr.io/aserper/rocketalert-bots:$(git rev-parse HEAD)
```

---

## Kubernetes Deployment

### Prerequisites

**1. Kubernetes Cluster:**
- minikube (local testing)
- k3s/k8s (self-hosted)
- GKE/EKS/AKS (cloud managed)

**2. kubectl Configuration:**
```bash
# Verify cluster connection
kubectl cluster-info

# Verify nodes
kubectl get nodes
```

**3. Container Registry Access:**
```bash
# Create pull secret for GHCR (if using private registry)
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=aserper \
  --docker-password=$GITHUB_TOKEN \
  --namespace=bots
```

### Namespace Creation

```bash
# Create namespace
kubectl create namespace bots

# Verify
kubectl get namespaces | grep bots
```

### Secret Management

**Option 1: Kubernetes Secrets (Recommended)**

```bash
# Create secret from literals
kubectl create secret generic rocketalert-secrets \
  --from-literal=ra-baseurl='https://ra-agg.kipodopik.com/api/v2/alerts' \
  --from-literal=custom-header-key='X-SECURITY-TOKEN' \
  --from-literal=custom-header-value='your_secret_token' \
  --from-literal=telegram-bot-token='8271024720:AAFrkR15ix...' \
  --from-literal=telegram-channel-id='@RocketAlert' \
  --from-literal=masto-baseurl='https://mastodon.social' \
  --from-literal=masto-access-token='x1C8wV94MO5vCbdjEE6C...' \
  --from-literal=mapbox-token='pk.eyJ1...' \
  --namespace=bots

# Verify secret
kubectl get secrets -n bots
kubectl describe secret rocketalert-secrets -n bots
```

**Option 2: From .env File**

```bash
# Create secret from file
kubectl create secret generic rocketalert-secrets \
  --from-env-file=.env \
  --namespace=bots
```

**Option 3: Sealed Secrets (GitOps-friendly)**

```bash
# Install sealed-secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.18.0/controller.yaml

# Install kubeseal CLI
wget https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.18.0/kubeseal-linux-amd64 -O kubeseal
sudo install -m 755 kubeseal /usr/local/bin/kubeseal

# Create sealed secret
kubectl create secret generic rocketalert-secrets \
  --from-literal=telegram-bot-token='8271024720:AAFrkR15ix...' \
  --dry-run=client -o yaml | \
  kubeseal -o yaml > sealed-secret.yaml

# Apply sealed secret
kubectl apply -f sealed-secret.yaml -n bots
```

### Deployment Manifest

**Create deployment YAML:**

```yaml
# rocketalert-deployment.yaml
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rocketalert-bots
  namespace: bots
  labels:
    app: rocketalert-bots
    version: v2.0.0
spec:
  replicas: 1  # Single instance (SSE connection is stateful)
  selector:
    matchLabels:
      app: rocketalert-bots
  template:
    metadata:
      labels:
        app: rocketalert-bots
        app.kubernetes.io/name: rocketalert-bots
        app.kubernetes.io/version: v2.0.0
    spec:
      imagePullSecrets:
      - name: ghcr-secret  # Remove if using public Docker Hub image
      containers:
      - name: rocketalert-bots
        image: ghcr.io/aserper/rocketalert-bots:latest
        imagePullPolicy: Always
        env:
        - name: TZ
          value: America/New_York
        - name: RA_BASEURL
          valueFrom:
            secretKeyRef:
              name: rocketalert-secrets
              key: ra-baseurl
        - name: CUSTOM_HEADER_KEY
          valueFrom:
            secretKeyRef:
              name: rocketalert-secrets
              key: custom-header-key
        - name: CUSTOM_HEADER_VALUE
          valueFrom:
            secretKeyRef:
              name: rocketalert-secrets
              key: custom-header-value
        - name: TELEGRAM_BOT_TOKEN
          valueFrom:
            secretKeyRef:
              name: rocketalert-secrets
              key: telegram-bot-token
        - name: TELEGRAM_CHANNEL_ID
          valueFrom:
            secretKeyRef:
              name: rocketalert-secrets
              key: telegram-channel-id
        - name: MASTO_BASEURL
          valueFrom:
            secretKeyRef:
              name: rocketalert-secrets
              key: masto-baseurl
        - name: MASTO_ACCESS_TOKEN
          valueFrom:
            secretKeyRef:
              name: rocketalert-secrets
              key: masto-access-token
        - name: MAPBOX_TOKEN
          valueFrom:
            secretKeyRef:
              name: rocketalert-secrets
              key: mapbox-token
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - |
              if [ ! -f /tmp/heartbeat ]; then exit 1; fi
              LAST=$(cat /tmp/heartbeat)
              NOW=$(date +%s)
              DIFF=$((NOW - ${LAST%.*}))
              if [ $DIFF -gt 90 ]; then exit 1; fi
              exit 0
          initialDelaySeconds: 120
          periodSeconds: 30
          failureThreshold: 3
          timeoutSeconds: 5
        readinessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - |
              if [ ! -f /tmp/heartbeat ]; then exit 1; fi
              LAST=$(cat /tmp/heartbeat)
              NOW=$(date +%s)
              DIFF=$((NOW - ${LAST%.*}))
              if [ $DIFF -gt 90 ]; then exit 1; fi
              exit 0
          initialDelaySeconds: 30
          periodSeconds: 10
          failureThreshold: 3
```

**Apply Deployment:**
```bash
kubectl apply -f rocketalert-deployment.yaml

# Verify deployment
kubectl get deployments -n bots
kubectl get pods -n bots

# View logs
kubectl logs -f deployment/rocketalert-bots -n bots
```

### Updating Deployment

**Rolling Update (new image):**
```bash
# Update image tag
kubectl set image deployment/rocketalert-bots \
  rocketalert-bots=ghcr.io/aserper/rocketalert-bots:$(git rev-parse HEAD) \
  -n bots

# Watch rollout
kubectl rollout status deployment/rocketalert-bots -n bots

# Verify new pod
kubectl get pods -n bots -o wide
```

**Update Secrets:**
```bash
# Delete old secret
kubectl delete secret rocketalert-secrets -n bots

# Create new secret
kubectl create secret generic rocketalert-secrets \
  --from-literal=telegram-bot-token='NEW_TOKEN' \
  ... \
  -n bots

# Restart deployment to pick up new secret
kubectl rollout restart deployment/rocketalert-bots -n bots
```

### Scaling & High Availability

⚠️ **Note:** Current design supports **only 1 replica** due to stateful SSE connection.

**For HA, use:**
- **PodDisruptionBudget** to ensure graceful shutdowns
- **Node affinity** to avoid co-location

```yaml
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: rocketalert-bots-pdb
  namespace: bots
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: rocketalert-bots
```

---

## ArgoCD GitOps Deployment

### Prerequisites

**1. ArgoCD Installation:**
```bash
# Install ArgoCD in cluster
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Install ArgoCD CLI
curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x /usr/local/bin/argocd

# Access ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

**2. Git Repository Setup:**
```bash
# Create deployments repository
git clone https://github.com/aserper/deployments.git
cd deployments

# Create manifests directory
mkdir -p rocketalert-bots
cd rocketalert-bots
```

### ArgoCD Application Manifest

**Create Application:**

```yaml
# argocd-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: rocketalert-bots
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/aserper/deployments.git
    targetRevision: main
    path: rocketalert-bots
  destination:
    server: https://kubernetes.default.svc
    namespace: bots
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
    - CreateNamespace=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

**Apply Application:**
```bash
kubectl apply -f argocd-app.yaml

# Verify application
argocd app list
argocd app get rocketalert-bots
```

### GitOps Workflow

**1. Update Image Tag:**
```bash
# Edit deployment manifest
cd deployments/rocketalert-bots
vim deployment.yaml

# Change image tag
# FROM: image: ghcr.io/aserper/rocketalert-bots:abc123
# TO:   image: ghcr.io/aserper/rocketalert-bots:def456

# Commit and push
git add deployment.yaml
git commit -m "Update rocketalert-bots to def456"
git push
```

**2. ArgoCD Auto-Sync:**
```
ArgoCD detects change in Git → Syncs to cluster → Rolling update
```

**3. Monitor Deployment:**
```bash
# Watch ArgoCD sync
argocd app sync rocketalert-bots --watch

# View application status
argocd app get rocketalert-bots

# View sync history
argocd app history rocketalert-bots
```

### Manual Sync & Rollback

**Manual Sync:**
```bash
# Force sync
argocd app sync rocketalert-bots

# Sync specific resource
argocd app sync rocketalert-bots --resource apps:Deployment:rocketalert-bots
```

**Rollback:**
```bash
# View history
argocd app history rocketalert-bots

# Rollback to previous revision
argocd app rollback rocketalert-bots 3  # Rollback to revision 3
```

---

## Configuration Management

### Environment-Specific Configs

**Directory Structure:**
```
deployments/
└── rocketalert-bots/
    ├── base/
    │   ├── deployment.yaml
    │   └── kustomization.yaml
    ├── overlays/
    │   ├── dev/
    │   │   ├── kustomization.yaml
    │   │   └── secrets.yaml
    │   ├── staging/
    │   │   ├── kustomization.yaml
    │   │   └── secrets.yaml
    │   └── production/
    │       ├── kustomization.yaml
    │       └── secrets.yaml
    └── README.md
```

**Kustomize Example:**

```yaml
# base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- deployment.yaml

# overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
bases:
- ../../base
patchesStrategicMerge:
- secrets.yaml
images:
- name: ghcr.io/aserper/rocketalert-bots
  newTag: v2.0.0
replicas:
- name: rocketalert-bots
  count: 1
```

**Deploy with Kustomize:**
```bash
kubectl apply -k overlays/production
```

### Secret Rotation

**Automated Rotation (External Secrets Operator):**

```yaml
# external-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: rocketalert-secrets
  namespace: bots
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: rocketalert-secrets
    creationPolicy: Owner
  data:
  - secretKey: telegram-bot-token
    remoteRef:
      key: rocketalert/telegram
      property: bot_token
```

**Manual Rotation:**
```bash
# 1. Generate new token (Telegram/Mastodon)
# 2. Update secret
kubectl create secret generic rocketalert-secrets \
  --from-literal=telegram-bot-token='NEW_TOKEN' \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Restart pods
kubectl rollout restart deployment/rocketalert-bots -n bots
```

---

## Health Checks & Monitoring

### Liveness Probe

**Purpose:** Detect hung processes (stuck SSE connection, deadlock)

**Mechanism:** Check `/tmp/heartbeat` file age

**Thresholds:**
- Initial delay: 120s (allow startup time)
- Period: 30s (check frequency)
- Timeout: 5s (probe execution limit)
- Failure threshold: 3 (restart after 3 failures = 90s of staleness)

**Manual Test:**
```bash
# Exec into pod
kubectl exec -it deployment/rocketalert-bots -n bots -- /bin/sh

# Check heartbeat age
cat /tmp/heartbeat
# Output: 1735587845.123456 (Unix timestamp)

# Calculate age
NOW=$(date +%s)
LAST=$(cat /tmp/heartbeat)
echo $((NOW - ${LAST%.*}))
# Output: 15 (seconds since last heartbeat)
```

### Readiness Probe

**Purpose:** Prevent traffic routing to unhealthy pods

**Configuration:** Same as liveness probe

**Usage:** Ensures pod is ready before adding to service endpoints

### Logging

**View Logs:**
```bash
# Stream logs
kubectl logs -f deployment/rocketalert-bots -n bots

# Last 100 lines
kubectl logs --tail=100 deployment/rocketalert-bots -n bots

# Logs since 1 hour ago
kubectl logs --since=1h deployment/rocketalert-bots -n bots

# Logs for previous pod instance
kubectl logs -p deployment/rocketalert-bots -n bots
```

**Structured Logging (Future Enhancement):**
```python
# Replace print() with structured logging
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

logger = logging.getLogger(__name__)

# Log as JSON
logger.info(json.dumps({
    "timestamp": datetime.now().isoformat(),
    "level": "INFO",
    "message": "Event received",
    "alert_type_id": event["alertTypeId"],
    "alert_count": len(event["alerts"])
}))
```

### Metrics (Prometheus Integration)

**Add Prometheus Exporter:**

```python
# Add to main.py
from prometheus_client import Counter, Histogram, start_http_server

events_received = Counter('rocketalert_events_received_total', 'Total events received')
alerts_processed = Counter('rocketalert_alerts_processed_total', 'Total alerts processed')
processing_time = Histogram('rocketalert_processing_seconds', 'Event processing time')

# Start metrics server
start_http_server(8000)

# Instrument code
events_received.inc()
with processing_time.time():
    messageManager.postMessage(eventData)
```

**ServiceMonitor (Prometheus Operator):**
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: rocketalert-bots
  namespace: bots
spec:
  selector:
    matchLabels:
      app: rocketalert-bots
  endpoints:
  - port: metrics
    interval: 30s
```

---

## Maintenance & Operations

### Updating Dependencies

**Local Update:**
```bash
# Edit requirements.in
vim requirements.in

# Compile new requirements.txt
pip-compile requirements.in

# Install updated dependencies
pip install -r requirements.txt

# Test
pytest

# Commit
git add requirements.in requirements.txt
git commit -m "Update dependencies"
```

**Trigger New Build:**
```bash
git push origin main
# GitHub Actions will run tests and build new Docker image
```

### Backup & Restore

**No Persistent State:**
- Application is stateless (no database, no session files)
- Only secrets need backup

**Backup Secrets:**
```bash
# Export secrets to file
kubectl get secret rocketalert-secrets -n bots -o yaml > rocketalert-secrets-backup.yaml

# Store securely (e.g., encrypted git repository, vault)
```

**Restore Secrets:**
```bash
kubectl apply -f rocketalert-secrets-backup.yaml
```

### Disaster Recovery

**Scenario: Cluster Failure**

1. Provision new cluster
2. Install ArgoCD
3. Restore secrets
4. Apply ArgoCD Application manifest
5. ArgoCD syncs from Git → Deployment restored

**RTO (Recovery Time Objective):** < 10 minutes
**RPO (Recovery Point Objective):** 0 (no data loss, stateless)

### Performance Tuning

**Reduce Latency:**
```python
# Adjust timeouts in rocket_alert_api.py
return requests.get(..., timeout=(5, 30))  # Faster connect/read
```

**Increase Throughput (Future):**
```python
# Enable async bot posting
async def post_message_async(event_data):
    await asyncio.gather(
        telegram_bot.send_message_async(text),
        mastodon_bot.send_message_async(text)
    )
```

### Troubleshooting Checklist

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for detailed debugging guide.

**Quick Checks:**
1. ✅ Environment variables set correctly?
2. ✅ Bot tokens valid?
3. ✅ Network connectivity to API?
4. ✅ Kubernetes pod running?
5. ✅ Heartbeat file updating?

---

## Appendix

### Helpful Commands

**Docker:**
```bash
# Remove old images
docker system prune -a

# Inspect container
docker inspect rocketalert-bots

# Container resource usage
docker stats rocketalert-bots
```

**Kubernetes:**
```bash
# Describe pod
kubectl describe pod <pod-name> -n bots

# Get events
kubectl get events -n bots --sort-by='.lastTimestamp'

# Pod resource usage
kubectl top pod -n bots

# Force delete pod
kubectl delete pod <pod-name> -n bots --force --grace-period=0
```

**ArgoCD:**
```bash
# Delete application
argocd app delete rocketalert-bots

# Refresh application (detect Git changes)
argocd app refresh rocketalert-bots

# Diff local vs cluster
argocd app diff rocketalert-bots
```

### References

- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Kustomize Documentation](https://kustomize.io/)

### Document Version

- **Version:** 1.0
- **Last Updated:** 2025-12-30
- **Author:** Setup & Deployment Guide
