# UptimePulse ⚡

> A lightweight, developer-first API and service health monitoring engine featuring synthetic assertions, SSL expiration auditing, and automated webhook alerts.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Architecture: Event-Driven](https://img.shields.io/badge/architecture-event--driven-green.svg)](README.md)

---

## 🎯 Why UptimePulse?

Traditional uptime monitors (like Uptime Kuma or Pingdom) are often heavy, GUI-monolithic applications designed for manual web clicking. 

**UptimePulse** is built for developers:
- **Code & Config-First (GitOps):** Declare all your endpoints, ping intervals, and assertion rules in a clean YAML configuration.
- **Deep Synthetic Assertions:** Don't just check `status == 200`. Validate JSON response keys, enforce maximum latency thresholds, and monitor SSL certificate expiration dates.
- **Ultra-Lightweight (<25MB RAM):** Runs seamlessly in the background as a daemon, Docker container, or CI/CD test step.
- **Developer-Centric Alerts:** Dispatches actionable incident payloads directly to Discord, Slack, or generic webhooks with exact error diagnostics.

---

## 🏗️ Architecture

```
                       ┌──────────────────────────┐
                       │   monitors.yaml Config   │
                       └────────────┬─────────────┘
                                    │
                                    ▼
                       ┌──────────────────────────┐
                       │     Scheduler Engine     │
                       └────────────┬─────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           ▼                        ▼                        ▼
┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐
│   HTTP/S Prober    │   │  TCP Socket Prober │   │  SSL Cert Auditor  │
│ (Status + Payload) │   │   (Port Health)    │   │ (Expiration Days)  │
└──────────┬─────────┘   └──────────┬─────────┘   └──────────┬─────────┘
           │                        │                        │
           └────────────────────────┼────────────────────────┘
                                    │
                                    ▼
                       ┌──────────────────────────┐
                       │  SQLite Time-Series DB   │
                       │ (Heartbeats & Incidents) │
                       └────────────┬─────────────┘
                                    │
                           [On Outage / Recovery]
                                    │
                                    ▼
                       ┌──────────────────────────┐
                       │ Webhook Dispatcher Engine│
                       │ (Discord, Slack, Custom) │
                       └──────────────────────────┘
```

---

## 📦 Installation & Setup

Clone the repository and install:

```bash
git clone https://github.com/princexav/uptimepulse.git
cd uptimepulse
pip install -e .
```

Or run directly without installation:

```bash
python -m uptimepulse.cli --help
```

---

## 🚀 Quickstart

### 1. Define Monitors (`monitors.yaml`)

```yaml
monitors:
  - id: "main-api"
    name: "Production REST API"
    type: "http"
    target: "https://httpbin.org/status/200"
    interval_seconds: 30
    timeout_seconds: 5
    assertions:
      expected_status: 200
      max_latency_ms: 1500

  - id: "postgres-port"
    name: "Primary Database Port"
    type: "tcp"
    target: "db.internal.net:5432"
    interval_seconds: 60
    timeout_seconds: 3

  - id: "web-cert"
    name: "Frontend SSL Certificate"
    type: "ssl"
    target: "example.com"
    interval_seconds: 3600
    assertions:
      min_days_remaining: 14
```

### 2. Run a One-Off Health Check

```bash
python -m uptimepulse.cli check --config monitors.yaml
```

Output:
```
[PASS] Production REST API (200 OK - 142ms)
[PASS] Primary Database Port (TCP open - 18ms)
[PASS] Frontend SSL Certificate (Valid - 68 days remaining)
```

### 3. Start the Background Monitor Engine

```bash
python -m uptimepulse.cli run --config monitors.yaml
```

---

## 🧪 Testing

Run the automated test suite:

```bash
python -m unittest discover -s tests
```

---

## 🗺️ Roadmap & Engineering Plan

We have an active development roadmap covering 20+ hours of planned engineering milestones (Prometheus metrics export, dead-man's switch, and automated status page generation). See [ROADMAP.md](ROADMAP.md).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
