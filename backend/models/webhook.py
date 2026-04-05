from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class WebhookEndpointCreate(BaseModel):
    url: str
    description: Optional[str] = None


class WebhookEndpointResponse(BaseModel):
    id: int
    url: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookEventResponse(BaseModel):
    id: int
    endpoint_id: int
    event_type: str
    status: str
    http_status: Optional[int]
    attempt: int
    fired_at: datetime

    class Config:
        from_attributes = True
