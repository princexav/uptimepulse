import unittest
import os
import uuid
from datetime import datetime, timezone
from uptimepulse.models import CheckResult
from uptimepulse.storage import UptimeStorage

class TestUptimeStorage(unittest.TestCase):
    def setUp(self):
        self.db_path = f"test_{uuid.uuid4().hex}.db"
        self.storage = UptimeStorage(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_record_heartbeat_and_uptime(self):
        now = datetime.now(timezone.utc)
        for _ in range(3):
            self.storage.record_heartbeat(CheckResult(
                monitor_id="api-1",
                timestamp=now,
                is_up=True,
                status_code=200,
                latency_ms=120.0
            ))
        self.storage.record_heartbeat(CheckResult(
            monitor_id="api-1",
            timestamp=now,
            is_up=False,
            status_code=500,
            latency_ms=250.0,
            error_message="HTTP 500 Internal Error"
        ))

        uptime = self.storage.calculate_uptime("api-1", hours=24)
        self.assertEqual(uptime, 75.0)

    def test_incident_lifecycle(self):
        now = datetime.now(timezone.utc)
        res_fail = CheckResult(
            monitor_id="api-1",
            timestamp=now,
            is_up=False,
            error_message="Connection timed out"
        )
        transition = self.storage.update_incident_state(res_fail)
        self.assertIsNotNone(transition)
        event, inc = transition
        self.assertEqual(event, "opened")
        self.assertEqual(inc.cause, "Connection timed out")
        self.assertTrue(inc.is_active)

        # Consecutive failure should NOT open duplicate incident
        transition_2 = self.storage.update_incident_state(res_fail)
        self.assertIsNone(transition_2)

        # Recovery resolves the incident
        res_ok = CheckResult(
            monitor_id="api-1",
            timestamp=now,
            is_up=True
        )
        transition_3 = self.storage.update_incident_state(res_ok)
        self.assertIsNotNone(transition_3)
        event_3, inc_3 = transition_3
        self.assertEqual(event_3, "resolved")
        self.assertFalse(inc_3.is_active)

if __name__ == "__main__":
    unittest.main()
