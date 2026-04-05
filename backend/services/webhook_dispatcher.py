import requests
import time
import threading
from datetime import datetime
from db.connection import SessionLocal

MAX_RETRIES = 3
BACKOFF_SECONDS = [0, 300, 1800]   # immediate, 5 min, 30 min


def _dispatch_to_endpoint(endpoint_id: int, endpoint_url: str,
                           event_type: str, payload: dict):
    """Attempt delivery to a single endpoint with retry logic."""
    db = SessionLocal()
    try:
        for attempt_idx, wait in enumerate(BACKOFF_SECONDS):
            if wait > 0:
                time.sleep(wait)

            try:
                resp = requests.post(
                    endpoint_url,
                    json={"event": event_type, "data": payload,
                          "timestamp": datetime.utcnow().isoformat()},
                    timeout=5
                )
                status = "delivered" if resp.status_code < 400 else "failed"
                http_status = resp.status_code
            except Exception as e:
                status = "failed"
                http_status = None

            db.execute(
                """INSERT INTO webhook_events
                   (endpoint_id, event_type, status, http_status, attempt)
                   VALUES (:eid, :etype, :status, :hstatus, :attempt)""",
                {
                    "eid": endpoint_id,
                    "etype": event_type,
                    "status": status,
                    "hstatus": http_status,
                    "attempt": attempt_idx + 1
                }
            )
            db.commit()

            if status == "delivered":
                break
    finally:
        db.close()


def dispatch(event_type: str, payload: dict):
    """
    Fire a webhook event to all registered endpoints.
    Runs in a background thread to avoid blocking the API response.
    Retries up to 3 times with exponential backoff: 0s → 5min → 30min.
    """
    db = SessionLocal()
    try:
        from sqlalchemy import text
        result = db.execute(text("SELECT id, url FROM webhook_endpoints"))
        endpoints = result.fetchall()
    finally:
        db.close()

    for endpoint in endpoints:
        thread = threading.Thread(
            target=_dispatch_to_endpoint,
            args=(endpoint[0], endpoint[1], event_type, payload),
            daemon=True
        )
        thread.start()
