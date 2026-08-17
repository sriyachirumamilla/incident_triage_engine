from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.alert import AlertCreate, IngestionResponse
from app.services.triage import TriageEngine
from app.services.deduplication import dedup_service

router = APIRouter()


@router.post("/ingest", response_model=IngestionResponse, status_code=status.HTTP_201_CREATED)
async def ingest_alert(
    alert_in: AlertCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    High-throughput alert ingestion endpoint.
    1. Computes SHA-256 fingerprint for the incoming alert.
    2. Deduplicates or creates new Incident/Alert in PostgreSQL.
    3. Offloads heavy AI enrichment to background task.
    """
    engine = TriageEngine(db)

    # 1. Compute SHA-256 fingerprint using your exact AlertCreate schema fields
    fingerprint = dedup_service.generate_fingerprint(
        source=alert_in.source,
        title=alert_in.title,
        service=alert_in.service,
        metadata=alert_in.metadata
    )

    # 2. Process alert in database
    incident = await engine.process_new_alert(alert_in)

    # 3. Offload AI enrichment to background task
    background_tasks.add_task(engine.enrich_incident, incident.id)

    # 4. Determine status for IngestionResponse
    res_status = "created" if str(incident.status).lower() == "open" else "deduplicated"

    return IngestionResponse(
        message="Alert processed successfully",
        alert_id=incident.id,
        fingerprint=fingerprint,
        status=res_status
    )