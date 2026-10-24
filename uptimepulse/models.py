from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime

@dataclass
class AssertionRules:
    expected_status: int = 200
    max_latency_ms: Optional[float] = None
    min_days_remaining: int = 14
    expected_body_substring: Optional[str] = None

@dataclass
class MonitorConfig:
    id: str
    name: str
    type: str # 'http', 'tcp', 'ssl'
    target: str
    interval_seconds: int = 60
    timeout_seconds: float = 5.0
    assertions: AssertionRules = field(default_factory=AssertionRules)

@dataclass
class CheckResult:
    monitor_id: str
    timestamp: datetime
    is_up: bool
    status_code: Optional[int] = None
    latency_ms: float = 0.0
    error_message: Optional[str] = None
    ssl_days_remaining: Optional[int] = None

@dataclass
class Incident:
    id: Optional[int]
    monitor_id: str
    started_at: datetime
    resolved_at: Optional[datetime]
    cause: str
    is_active: bool = True
