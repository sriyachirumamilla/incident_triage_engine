#tests full flow - API -> DB -> Background Task trigger

import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_alert_ingestion_flow(db_session):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        alert_payload = {
            "title": "Database Connection Timeout",
            "description": "Postgres is not responding on port 5432",
            "source": "grafana",
            "severity": "critical",
            "service": "database",
            "metadata": {"env": "production"}
        }
        
        response = await ac.post("/api/v1/alerts/ingest", json=alert_payload)
        
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "queued"
    assert "alert_id" in data