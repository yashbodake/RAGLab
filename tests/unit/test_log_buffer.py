import pytest
import threading
from backend.services.log_buffer import LogBuffer

@pytest.mark.unit
def test_append_and_flush():
    """Appended entries are returned by flush_query_logs."""
    buf = LogBuffer()
    buf.start_query()
    buf.append("retrieval", "Starting search", "info")
    buf.append("bm25", "Finished search", "debug")
    
    logs = buf.flush_query_logs()
    assert len(logs) == 2
    assert logs[0].stage == "retrieval"
    assert logs[0].message == "Starting search"
    assert logs[0].level == "info"
    assert logs[1].stage == "bm25"
    assert logs[1].message == "Finished search"
    assert logs[1].level == "debug"
    
    # Verify that query logs are empty after flush
    assert len(buf.flush_query_logs()) == 0

@pytest.mark.unit
def test_ring_buffer_max_size():
    """Buffer does not exceed max_size."""
    buf = LogBuffer(max_size=5)
    for i in range(10):
        buf.append("stage", f"msg {i}")
        
    all_logs = buf.get_all_logs()
    assert len(all_logs) == 5
    assert all_logs[0].message == "msg 5"
    assert all_logs[-1].message == "msg 9"

@pytest.mark.unit
def test_start_query_resets():
    """start_query clears per-query logs."""
    buf = LogBuffer()
    buf.append("stage", "msg")
    buf.start_query()
    assert len(buf.flush_query_logs()) == 0
    
    # Ring buffer is not cleared by start_query, only query-specific logs
    assert len(buf.get_all_logs()) == 1

