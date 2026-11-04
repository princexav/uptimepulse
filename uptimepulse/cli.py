import sys
import os
import argparse
import time
from datetime import datetime
from typing import List
from .models import MonitorConfig, AssertionRules
from .checker import probe_monitor
from .storage import UptimeStorage
from .alerts import AlertDispatcher

def load_simple_config(path: str) -> List[MonitorConfig]:
    """Lightweight config loader supporting JSON and basic YAML."""
    if not os.path.exists(path):
        # Default mock monitors if config file not found
        return [
            MonitorConfig(
                id="example-http",
                name="Example HTTP Check",
                type="http",
                target="https://httpbin.org/status/200",
                timeout_seconds=5.0
            ),
            MonitorConfig(
                id="dns-tcp",
                name="Cloudflare DNS TCP",
                type="tcp",
                target="1.1.1.1:53",
                timeout_seconds=3.0
            ),
            MonitorConfig(
                id="github-ssl",
                name="GitHub TLS Audit",
                type="ssl",
                target="github.com",
                assertions=AssertionRules(min_days_remaining=14)
            )
        ]

    # If PyYAML is available, use it, otherwise parse basic JSON
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except ImportError:
        import json
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

    monitors = []
    for item in data.get("monitors", []):
        assertions_data = item.get("assertions", {})
        assertions = AssertionRules(
            expected_status=assertions_data.get("expected_status", 200),
            max_latency_ms=assertions_data.get("max_latency_ms"),
            min_days_remaining=assertions_data.get("min_days_remaining", 14),
            expected_body_substring=assertions_data.get("expected_body_substring")
        )
        monitors.append(MonitorConfig(
            id=item["id"],
            name=item.get("name", item["id"]),
            type=item.get("type", "http"),
            target=item["target"],
            interval_seconds=item.get("interval_seconds", 60),
            timeout_seconds=item.get("timeout_seconds", 5.0),
            assertions=assertions
        ))
    return monitors

def cmd_check(args):
    monitors = load_simple_config(args.config)
    storage = UptimeStorage(args.db)
    
    print(f"\n⚡ UptimePulse Check Run ({len(monitors)} monitors configured)")
    print("=" * 65)

    for m in monitors:
        res = probe_monitor(m)
        storage.record_heartbeat(res)
        storage.update_incident_state(res)
        
        status_tag = "PASS" if res.is_up else "FAIL"
        extra = f"{res.latency_ms:.1f}ms"
        if res.status_code:
            extra = f"HTTP {res.status_code} - {extra}"
        if res.ssl_days_remaining is not None:
            extra += f" - {res.ssl_days_remaining}d SSL remaining"
        if not res.is_up:
            extra += f" - Error: {res.error_message}"

        print(f"[{status_tag}] {m.name} ({m.target}) -> {extra}")

    print("=" * 65 + "\n")

def cmd_status(args):
    storage = UptimeStorage(args.db)
    monitors = load_simple_config(args.config)

    print("\n📊 24-Hour Service Availability Summary:")
    print("=" * 65)
    for m in monitors:
        uptime_pct = storage.calculate_uptime(m.id, hours=24)
        print(f" • {m.name.ljust(25)} : {uptime_pct}% uptime (past 24h)")
    print("=" * 65 + "\n")

def main():
    parser = argparse.ArgumentParser(
        prog="uptimepulse",
        description="Lightweight, developer-first API and service health monitoring engine."
    )
    parser.add_argument("--config", default="monitors.example.yaml", help="Path to monitors config file")
    parser.add_argument("--db", default="uptimepulse.db", help="Path to SQLite database")

    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="Run a single audit check across all monitors")
    status_parser = subparsers.add_parser("status", help="Print uptime percentage metrics for all monitors")

    args = parser.parse_args()

    if args.command == "check":
        cmd_check(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        cmd_check(args)

if __name__ == "__main__":
    main()
