import time
import socket
import ssl
from datetime import datetime, timezone
import urllib.request
import urllib.error
from .models import MonitorConfig, CheckResult

def check_http(config: MonitorConfig) -> CheckResult:
    start = time.perf_counter()
    req = urllib.request.Request(
        config.target,
        headers={"User-Agent": "UptimePulse/0.1.0"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=config.timeout_seconds) as response:
            latency_ms = (time.perf_counter() - start) * 1000.0
            status_code = response.status
            body = response.read(1024 * 64).decode("utf-8", errors="ignore")
            now = datetime.now(timezone.utc)
            
            # Evaluate assertions
            if status_code != config.assertions.expected_status:
                return CheckResult(
                    monitor_id=config.id,
                    timestamp=now,
                    is_up=False,
                    status_code=status_code,
                    latency_ms=latency_ms,
                    error_message=f"Expected status {config.assertions.expected_status}, received {status_code}"
                )
            
            if config.assertions.max_latency_ms and latency_ms > config.assertions.max_latency_ms:
                return CheckResult(
                    monitor_id=config.id,
                    timestamp=now,
                    is_up=False,
                    status_code=status_code,
                    latency_ms=latency_ms,
                    error_message=f"Latency {latency_ms:.1f}ms exceeded max {config.assertions.max_latency_ms}ms"
                )

            if config.assertions.expected_body_substring and config.assertions.expected_body_substring not in body:
                return CheckResult(
                    monitor_id=config.id,
                    timestamp=now,
                    is_up=False,
                    status_code=status_code,
                    latency_ms=latency_ms,
                    error_message=f"Body missing expected substring '{config.assertions.expected_body_substring}'"
                )

            return CheckResult(
                monitor_id=config.id,
                timestamp=now,
                is_up=True,
                status_code=status_code,
                latency_ms=latency_ms
            )

    except urllib.error.HTTPError as e:
        latency_ms = (time.perf_counter() - start) * 1000.0
        is_up = (e.code == config.assertions.expected_status)
        return CheckResult(
            monitor_id=config.id,
            timestamp=datetime.now(timezone.utc),
            is_up=is_up,
            status_code=e.code,
            latency_ms=latency_ms,
            error_message=None if is_up else f"HTTP Error {e.code}: {e.reason}"
        )
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000.0
        return CheckResult(
            monitor_id=config.id,
            timestamp=datetime.now(timezone.utc),
            is_up=False,
            latency_ms=latency_ms,
            error_message=str(e)
        )

def check_tcp(config: MonitorConfig) -> CheckResult:
    start = time.perf_counter()
    try:
        if ":" in config.target:
            host, port_str = config.target.split(":", 1)
            port = int(port_str)
        else:
            host = config.target
            port = 80

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(config.timeout_seconds)
        sock.connect((host, port))
        sock.close()
        latency_ms = (time.perf_counter() - start) * 1000.0

        return CheckResult(
            monitor_id=config.id,
            timestamp=datetime.now(timezone.utc),
            is_up=True,
            latency_ms=latency_ms
        )
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000.0
        return CheckResult(
            monitor_id=config.id,
            timestamp=datetime.now(timezone.utc),
            is_up=False,
            latency_ms=latency_ms,
            error_message=f"TCP connection failed: {e}"
        )

def check_ssl(config: MonitorConfig) -> CheckResult:
    start = time.perf_counter()
    hostname = config.target.replace("https://", "").replace("http://", "").split("/")[0]
    if ":" in hostname:
        hostname = hostname.split(":")[0]

    ctx = ssl.create_default_context()
    now = datetime.now(timezone.utc)
    try:
        with socket.create_connection((hostname, 443), timeout=config.timeout_seconds) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                latency_ms = (time.perf_counter() - start) * 1000.0
                
                not_after_str = cert.get("notAfter")
                if not not_after_str:
                    return CheckResult(
                        monitor_id=config.id,
                        timestamp=now,
                        is_up=False,
                        latency_ms=latency_ms,
                        error_message="Could not extract certificate expiration date"
                    )

                expires_at = datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                days_left = (expires_at - now).days

                if days_left < config.assertions.min_days_remaining:
                    return CheckResult(
                        monitor_id=config.id,
                        timestamp=now,
                        is_up=False,
                        latency_ms=latency_ms,
                        ssl_days_remaining=days_left,
                        error_message=f"SSL certificate expires in {days_left} days (threshold is {config.assertions.min_days_remaining})"
                    )

                return CheckResult(
                    monitor_id=config.id,
                    timestamp=now,
                    is_up=True,
                    latency_ms=latency_ms,
                    ssl_days_remaining=days_left
                )

    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000.0
        return CheckResult(
            monitor_id=config.id,
            timestamp=now,
            is_up=False,
            latency_ms=latency_ms,
            error_message=f"SSL audit failed: {e}"
        )

def probe_monitor(config: MonitorConfig) -> CheckResult:
    m_type = config.type.lower()
    if m_type == "http" or m_type == "https":
        return check_http(config)
    elif m_type == "tcp":
        return check_tcp(config)
    elif m_type == "ssl":
        return check_ssl(config)
    else:
        return CheckResult(
            monitor_id=config.id,
            timestamp=datetime.now(timezone.utc),
            is_up=False,
            error_message=f"Unsupported monitor type: {config.type}"
        )
