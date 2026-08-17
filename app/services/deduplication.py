# ensures if the same error hits 50 times, to process the AI logic once
import hashlib
import json
from typing import Dict, Any

class DeduplicationService:
    @staticmethod
    def generate_fingerprint(source: str, title: str, service: str, metadata: Dict[str, Any]) -> str:
        """
        Generates a deterministic SHA-256 hash. 
        to use specific fields to identify 'uniqueness'.
        """
        # sort the dictionary to ensure the hash is identical even if 
        # keys arrive in a different order from the source.
        stable_metadata = json.dumps(metadata, sort_keys = True)

        payload = f"{source.lower()} | {title.lower()} | {service.lower()} | {stable_metadata}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
dedup_service = DeduplicationService()