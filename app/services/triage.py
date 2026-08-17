import json
import logging
from uuid import UUID
from typing import Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.redis import get_redis
from app.models.incident import Incident, Alert, SeverityEnum, IncidentStatusEnum
from app.schemas.alert import AlertCreate
from app.services.deduplication import dedup_service
from app.services.embedding import embedding_service
from app.services.llm import llm_service

logger = logging.getLogger(__name__)


class TriageEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_new_alert(self, alert_data: AlertCreate) -> Incident:
        """
        The main workflow:
        1. Extract & normalize alert payload fields.
        2. Generate SHA-256 fingerprint.
        3. Check for an existing open incident via linked Alert fingerprints.
        4. Generate pgvector 384-dim vector embedding.
        5. Save Incident & Alert transactionally to PostgreSQL.
        """
        alert_dict = alert_data.model_dump()

        # Extract and normalize fields to handle potential typo variations cleanly
        title = alert_dict.get("title", "Untitled Alert")
        description = (
            alert_dict.get("description")
            or alert_dict.get("desription")
            or "No description provided"
        )
        source = alert_dict.get("source", "system")
        service_name = (
            alert_dict.get("service")
            or alert_dict.get("service_name")
            or "unknown-service"
        )
        severity_val = str(
            alert_dict.get("severity") or alert_dict.get("serverity") or "medium"
        ).lower()
        metadata = alert_dict.get("metadata", {})

        # Map string severity to SeverityEnum
        severity_map = {
            "p1": SeverityEnum.CRITICAL,
            "critical": SeverityEnum.CRITICAL,
            "p2": SeverityEnum.HIGH,
            "high": SeverityEnum.HIGH,
            "p3": SeverityEnum.MEDIUM,
            "medium": SeverityEnum.MEDIUM,
            "p4": SeverityEnum.LOW,
            "low": SeverityEnum.LOW,
        }
        mapped_severity = severity_map.get(severity_val, SeverityEnum.MEDIUM)

        # 1. Generate Fingerprint
        fingerprint = dedup_service.generate_fingerprint(
            source=source,
            title=title,
            service=service_name,
            metadata=metadata
        )

        # 2. Check for existing active incident linked to this alert fingerprint
        existing_incident = await self._get_existing_incident(fingerprint)
        if existing_incident:
            # Create duplicate alert record linked to the existing open incident
            duplicate_alert = Alert(
                service_name=service_name,
                environment=metadata.get("environment", "production"),
                error_message=f"{title}: {description}",
                fingerprint=fingerprint,
                incident_id=existing_incident.id,
                payload=alert_dict
            )
            self.db.add(duplicate_alert)
            await self.db.commit()
            return existing_incident

        # 3. If new, generate AI Vector Embedding
        combined_text = f"{title} {description}"
        vector = embedding_service.generate_vector(combined_text)

        # 4. Create Incident record
        new_incident = Incident(
            title=title,
            description=description,
            severity=mapped_severity,
            status=IncidentStatusEnum.OPEN,
            embedding=vector,
            metadata_json=metadata
        )
        self.db.add(new_incident)
        await self.db.flush()  # Flushes session to generate new_incident.id UUID

        # 5. Create associated Alert record
        new_alert = Alert(
            service_name=service_name,
            environment=metadata.get("environment", "production"),
            error_message=f"{title}: {description}",
            fingerprint=fingerprint,
            incident_id=new_incident.id,
            payload=alert_dict
        )
        self.db.add(new_alert)

        await self.db.commit()
        await self.db.refresh(new_incident)

        return new_incident

    async def _get_existing_incident(self, fingerprint: str) -> Optional[Incident]:

        """
        Look up an existing alert by SHA-256 fingerprint.
        If found and attached to an incident, return that incident.
        """
        stmt = (
            select(Alert)
            .where(Alert.fingerprint == fingerprint)
            .order_by(Alert.received_at.desc())
        )
        result = await self.db.execute(stmt)
        
        # FIX: Use .scalars().first() instead of .scalar_one_or_none()
        existing_alert = result.scalars().first()

        if existing_alert and existing_alert.incident_id:
            incident_stmt = select(Incident).where(Incident.id == existing_alert.incident_id)
            incident_result = await self.db.execute(incident_stmt)
            return incident_result.scalars().first()

        return None

    async def find_similar_incidents(
        self, incident_id: UUID, limit: int = 5, threshold: float = 0.4
    ) -> List[Tuple[Incident, float]]:
        """Finds historical resolved incidents semantically similar to the given incident."""
        target_stmt = select(Incident).where(Incident.id == incident_id)
        result = await self.db.execute(target_stmt)
        target = result.scalar_one_or_none()

        if not target or target.embedding is None:
            return []

        # Vector Search using pgvector cosine distance
        distance_fn = Incident.embedding.cosine_distance(target.embedding)

        stmt = (
            select(Incident, (1 - distance_fn).label("similarity"))
            .where(Incident.id != incident_id)
            .where(Incident.status == IncidentStatusEnum.RESOLVED)
            .where(distance_fn < threshold)
            .order_by(distance_fn.asc())
            .limit(limit)
        )

        results = await self.db.execute(stmt)
        return results.all()

    async def get_cached_similarity(self, incident_id: UUID):
        """Fetches cached similarity results from Redis."""
        redis = await get_redis()
        cache_key = f"sim:{incident_id}"
        cached_data = await redis.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        return None

    async def enrich_incident(self, incident_id: UUID):
        """Async task to enrich incident with AI root-cause summary and remediation steps."""
        stmt = select(Incident).where(Incident.id == incident_id)
        result = await self.db.execute(stmt)
        incident = result.scalar_one_or_none()

        if not incident:
            return

        summary = await llm_service.summarize_incident(incident.title, incident.description)

        incident.ai_rca_summary = summary
        await self.db.commit()
        logger.info(f"Enriched incident {incident_id} with AI summary.")