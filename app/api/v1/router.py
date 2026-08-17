#add New Incidents endpoint to API Router
from fastapi import APIRouter
from app.api.v1.endpoints import alerts, incidents

api_router = APIRouter()
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])