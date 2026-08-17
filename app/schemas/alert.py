# Raw signals from monitoring tools

from datetime import datetime
from typing import  Any, Dict, Optional
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class AlertBase(BaseModel):
    title: str = Field(..., examples=["High Latency on Checkout API"])
    description: str = Field(..., examples=["P99 lateny > 1.5s in us-east-1"])
    source: str = Field(..., examples=["promethus"])
    severity: AlertSeverity = AlertSeverity.MEDIUM
    service: str = Field(..., examples=["chekout-service"])
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AlertCreate(AlertBase):
    pass

class AlertRead(AlertBase):
    """Output schemas for individual alert"""
    model_config = ConfigDict (from_attributes=True)

    id: UUID
    fingerprint: str
    created_at:  datetime

class IngestionResponse(BaseModel):
    """Response schema for alert ingestion endpoint"""
    message: str
    alert_id: UUID
    fingerprint: str
    status: str
