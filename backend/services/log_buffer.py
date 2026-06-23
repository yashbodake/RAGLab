import threading
from collections import deque
from datetime import datetime, timezone
from backend.models.schemas import LogEntry

class LogBuffer:
    """Thread-safe ring buffer for pipeline logs."""

    def __init__(self, max_size: int = 500):
        self._max_size = max_size
        self._buffer: deque[LogEntry] = deque(maxlen=max_size)
        self._query_logs: list[LogEntry] = []  # Current query's logs
        self._lock = threading.Lock()

    def start_query(self):
        """Reset per-query log collection."""
        with self._lock:
            self._query_logs = []

    def append(self, stage: str, message: str, level: str = "info"):
        """Append log entry thread-safely."""
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            stage=stage,
            message=message,
            level=level,
        )
        with self._lock:
            self._buffer.append(entry)
            self._query_logs.append(entry)

    def flush_query_logs(self) -> list[LogEntry]:
        """Return and clear current query's logs."""
        with self._lock:
            logs = self._query_logs.copy()
            self._query_logs = []
            return logs

    def get_all_logs(self) -> list[LogEntry]:
        """Return all logs in the ring buffer."""
        with self._lock:
            return list(self._buffer)
