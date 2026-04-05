from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from db.connection import get_db
from models.webhook import WebhookEndpointCreate

router = APIRouter()


@router.post("/register", response_model=dict, status_code=201)
def register_endpoint(endpoint: WebhookEndpointCreate, db: Session = Depends(get_db)):
    """Register a URL to receive webhook events."""
    result = db.execute(
        text("INSERT INTO webhook_endpoints (url, description) VALUES (:url, :desc)"),
        {"url": endpoint.url, "desc": endpoint.description}
    )
    db.commit()
    endpoint_id = result.lastrowid

    row = db.execute(
        text("SELECT * FROM webhook_endpoints WHERE id = :id"), {"id": endpoint_id}
    ).fetchone()

    return {
        "id": row[0], "url": row[1], "description": row[2], "created_at": str(row[3])
    }


@router.get("/endpoints", response_model=list)
def list_endpoints(db: Session = Depends(get_db)):
    """List all registered webhook endpoints."""
    rows = db.execute(
        text("SELECT * FROM webhook_endpoints ORDER BY created_at DESC")
    ).fetchall()
    return [
        {"id": r[0], "url": r[1], "description": r[2], "created_at": str(r[3])}
        for r in rows
    ]


@router.delete("/endpoints/{endpoint_id}", response_model=dict)
def delete_endpoint(endpoint_id: int, db: Session = Depends(get_db)):
    """Remove a webhook endpoint."""
    row = db.execute(
        text("SELECT id FROM webhook_endpoints WHERE id = :id"), {"id": endpoint_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    db.execute(
        text("DELETE FROM webhook_endpoints WHERE id = :id"), {"id": endpoint_id}
    )
    db.commit()
    return {"message": f"Endpoint {endpoint_id} removed"}


@router.get("/events", response_model=list)
def list_events(db: Session = Depends(get_db)):
    """List recent webhook delivery events."""
    rows = db.execute(
        text("""
            SELECT we.*, wep.url
            FROM webhook_events we
            JOIN webhook_endpoints wep ON we.endpoint_id = wep.id
            ORDER BY we.fired_at DESC
            LIMIT 100
        """)
    ).fetchall()
    return [
        {
            "id": r[0], "endpoint_id": r[1], "event_type": r[2],
            "status": r[3], "http_status": r[4], "attempt": r[5],
            "fired_at": str(r[6]), "endpoint_url": r[7]
        }
        for r in rows
    ]
