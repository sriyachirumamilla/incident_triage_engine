#Testing the deduplication logic - using pytest and pytest-asyncio
import pytest
from app.services.deduplication import dedup_service

def test_fingerprint_consistency():
    """Ensure the same input always produces the same hash."""
    payload = {
        "source": "prometheus",
        "title": "High CPU",
        "service": "api",
        "metadata": {"cluster": "prod-01"}
    }
    
    hash1 = dedup_service.generate_fingerprint(**payload)
    hash2 = dedup_service.generate_fingerprint(**payload)
    
    assert hash1 == hash2

def test_fingerprint_normalization():
    """Ensure casing and spacing don't create duplicate incidents."""
    hash1 = dedup_service.generate_fingerprint("Prometheus", "High CPU", "API", {})
    hash2 = dedup_service.generate_fingerprint("prometheus ", "HIGH cpu", "api", {})
    
    assert hash1 == hash2