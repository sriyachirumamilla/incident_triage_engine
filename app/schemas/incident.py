#AI-enriched incidents and triage data
#Includes fields for AI Triage, such as vector-based similarity and automated priority.
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from .alert import AlertSeverity

class IncidentStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    DUPLICATE = "duplicate"

class IncidentBase(BaseModel):
    title: str
    summary: Optional[str] = Field(None, description="AI-generated summary of the incident")
    priority: Optional[str] = Field(None, description="AI-generated priority of the incident")
    status: IncidentStatus = IncidentStatus.OPEN

class IncidentCreate(IncidentBase):
    fingerprint: str
    raw_text: str

class IncidentUpdate(BaseModel):
    status: Optional[IncidentStatus] = None
    summary: Optional[str] = None
    priority: Optional[str] = None

class IncidentPublic(IncidentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    fingerprint: str
    created_at: datetime
    updated_at: datetime

class IncidentSimilarity(IncidentPublic):
    """Used for AI-powered 'Similar Incidents' features"""
    similarity_score: float = Field(..., description="Cosine similarity score (0-1)")