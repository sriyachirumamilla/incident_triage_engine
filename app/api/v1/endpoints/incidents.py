#Allows to query the details of an incident and to see it's AI-suggested "related" issue
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.core.database import get_db
from app.schemas.incident import IncidentPublic, IncidentSimilarity, IncidentUpdate
from app.services.triage import TriageEngine
from app.models.incident import Incident
from sqlalchemy import select

router = APIRouter()

@router.get("/{incident_id}", response_model=IncidentPublic)
async def get_incident(incident_id: UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Incident).where(Incident.id == incident_id)
    result = await db.execute(stmt)
    incident = result.scalar_one_or_none()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@router.get("/{incident_id}/similar", response_model=List[IncidentSimilarity])
async def get_similar_incidents(
    incident_id: UUID,
    limit: int = Query(5, gt=0, le=20),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns semantically similar historical incidents.
    """
    engine = TriageEngine(db)
    results = await engine.find_similar_incidents(incident_id, limit=limit)
    
    # Map SQLAlchemy row results to Pydantic schema
    return [
        IncidentSimilarity(
            **row.Incident.__dict__, 
            similarity_score=round(row.similarity, 4)
        ) for row in results
    ]

@router.patch("/{incident_id}", response_model=IncidentPublic)
async def update_incident(
    incident_id: UUID,
    incident_update: IncidentUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update incident status or manually override AI summary/priority.
    """
    stmt = select(Incident).where(Incident.id == incident_id)
    result = await db.execute(stmt)
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Apply updates dynamically
    update_data = incident_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(incident, field, value)

    await db.commit()
    await db.refresh(incident)
    return incident
