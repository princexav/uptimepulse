import unittest
from datetime import datetime, timezone
from uptimepulse.models import MonitorConfig, AssertionRules, CheckResult

class TestModels(unittest.TestCase):
    def test_monitor_config_defaults(self):
        m = MonitorConfig(
            id="test-1",
            name="Test Monitor",
            type="http",
            target="https://example.com"
        )
        self.assertEqual(m.interval_seconds, 60)
        self.assertEqual(m.timeout_seconds, 5.0)
        self.assertEqual(m.assertions.expected_status, 200)

    def test_check_result_attributes(self):
        now = datetime.now(timezone.utc)
        res = CheckResult(
            monitor_id="test-1",
            timestamp=now,
            is_up=True,
            status_code=200,
            latency_ms=45.2
        )
        self.assertTrue(res.is_up)
        self.assertEqual(res.status_code, 200)
        self.assertAlmostEqual(res.latency_ms, 45.2)

if __name__ == "__main__":
    unittest.main()
