import json

def sse_event(event_type: str, data: dict) -> str:
    """
    Format a Server-Sent Events (SSE) block.

    Args:
        event_type: The name/type of the event.
        data: The payload dictionary to serialize to JSON.

    Returns:
        Formatted event string.
    """
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
