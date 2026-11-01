import json
import urllib.request
import urllib.error
from typing import Dict, Any, List
from .models import Incident

class AlertDispatcher:
    def __init__(self, webhook_urls: List[str] = None):
        self.webhook_urls = webhook_urls or []

    def dispatch(self, event_type: str, incident: Incident) -> bool:
        """
        Dispatches an incident event ('opened' or 'resolved') to all registered webhooks.
        """
        if not self.webhook_urls:
            return False

        color = 0xFF0000 if event_type == "opened" else 0x00FF00
        title = f"🚨 Outage Detected: {incident.monitor_id}" if event_type == "opened" else f"✅ Service Recovered: {incident.monitor_id}"
        description = (
            f"**Cause:** {incident.cause}\n"
            f"**Time:** {incident.started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )

        # Discord / Slack compatible JSON payload
        payload = {
            "username": "UptimePulse Bot",
            "content": f"**[{event_type.upper()}]** {incident.monitor_id} - {incident.cause}",
            "embeds": [
                {
                    "title": title,
                    "description": description,
                    "color": color,
                    "timestamp": incident.started_at.isoformat()
                }
            ]
        }

        data = json.dumps(payload).encode("utf-8")
        success = True

        for url in self.webhook_urls:
            try:
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={"Content-Type": "application/json", "User-Agent": "UptimePulse-Alerts/0.1.0"}
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    pass
            except Exception as e:
                success = False

        return success
