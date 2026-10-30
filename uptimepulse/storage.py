import sqlite3
from typing import List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from .models import CheckResult, Incident

class UptimeStorage:
    def __init__(self, db_path: str = "uptimepulse.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS heartbeats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        monitor_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        is_up INTEGER NOT NULL,
                        status_code INTEGER,
                        latency_ms REAL,
                        error_message TEXT,
                        ssl_days_remaining INTEGER
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS incidents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        monitor_id TEXT NOT NULL,
                        started_at TEXT NOT NULL,
                        resolved_at TEXT,
                        cause TEXT NOT NULL,
                        is_active INTEGER NOT NULL DEFAULT 1
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_hb_mon_time ON heartbeats(monitor_id, timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_inc_mon_active ON incidents(monitor_id, is_active)")
        finally:
            conn.close()

    def record_heartbeat(self, result: CheckResult):
        conn = self._get_conn()
        try:
            with conn:
                conn.execute("""
                    INSERT INTO heartbeats (
                        monitor_id, timestamp, is_up, status_code, latency_ms, error_message, ssl_days_remaining
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.monitor_id,
                    result.timestamp.isoformat(),
                    1 if result.is_up else 0,
                    result.status_code,
                    result.latency_ms,
                    result.error_message,
                    result.ssl_days_remaining
                ))
        finally:
            conn.close()

    def update_incident_state(self, result: CheckResult) -> Optional[Tuple[str, Incident]]:
        conn = self._get_conn()
        try:
            with conn:
                cursor = conn.execute("""
                    SELECT id, monitor_id, started_at, resolved_at, cause, is_active
                    FROM incidents
                    WHERE monitor_id = ? AND is_active = 1
                    ORDER BY id DESC LIMIT 1
                """, (result.monitor_id,))
                row = cursor.fetchone()

                if not result.is_up:
                    if not row:
                        now_str = result.timestamp.isoformat()
                        cur = conn.execute("""
                            INSERT INTO incidents (monitor_id, started_at, cause, is_active)
                            VALUES (?, ?, ?, 1)
                        """, (result.monitor_id, now_str, result.error_message or "Unknown failure"))
                        inc_id = cur.lastrowid
                        return ("opened", Incident(
                            id=inc_id,
                            monitor_id=result.monitor_id,
                            started_at=result.timestamp,
                            resolved_at=None,
                            cause=result.error_message or "Unknown failure",
                            is_active=True
                        ))
                else:
                    if row:
                        resolved_str = result.timestamp.isoformat()
                        conn.execute("""
                            UPDATE incidents
                            SET resolved_at = ?, is_active = 0
                            WHERE id = ?
                        """, (resolved_str, row["id"]))
                        return ("resolved", Incident(
                            id=row["id"],
                            monitor_id=row["monitor_id"],
                            started_at=datetime.fromisoformat(row["started_at"]),
                            resolved_at=result.timestamp,
                            cause=row["cause"],
                            is_active=False
                        ))
            return None
        finally:
            conn.close()

    def calculate_uptime(self, monitor_id: str, hours: int = 24) -> float:
        now = datetime.now(timezone.utc)
        cutoff = (now - timedelta(hours=hours)).isoformat()
        conn = self._get_conn()
        try:
            cursor = conn.execute("""
                SELECT COUNT(*) as total, SUM(is_up) as up_count
                FROM heartbeats
                WHERE monitor_id = ? AND timestamp >= ?
            """, (monitor_id, cutoff))
            row = cursor.fetchone()
            total = row["total"] or 0
            up_count = row["up_count"] or 0
            if total == 0:
                return 100.0
            return round((up_count / total) * 100.0, 2)
        finally:
            conn.close()
