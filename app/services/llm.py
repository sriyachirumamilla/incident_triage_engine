import logging
from typing import Optional, Dict
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """
    Handles AI-powered summarization and priority classification.
    Can be easily swapped for OpenAI, Anthropic, or local Ollama.
    """
    
    async def summarize_incident(self, title: str, description: str) -> str:
        """
        Generates a concise technical summary for engineers.
        """
        # In a real scenario:
        # response = await openai_client.chat.completions.create(...)
        # return response.choices[0].message.content
        
        # Simulated logic for the Project:
        return f"AI Summary: This incident affects {title}. The root cause appears to be related to technical anomalies described as: {description[:50]}..."

    async def classify_priority(self, title: str, metadata: Dict) -> str:
        """
        AI logic to determine priority based on service criticality.
        """
        critical_services = ["auth", "payment", "gateway"]
        
        # Simple heuristic + AI logic simulation
        if any(service in title.lower() for service in critical_services):
            return "P0"
        return "P2"

llm_service = LLMService()