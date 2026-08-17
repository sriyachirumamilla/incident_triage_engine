# 🚀 AI-Powered Incident Management & Automated Triage Engine

An enterprise-grade, microservice-ready incident triage and deduplication engine built with **FastAPI**, **PostgreSQL (pgvector)**, **Redis**, and **SentenceTransformers**.

Designed to solve **Alert Fatigue** in high-throughput cloud environments by deduplicating noisy telemetry alerts in $O(1)$ time, computing 384-dimensional vector embeddings, and performing sub-millisecond semantic similarity search across historical outages.

---

## 📐 Architecture Overview

```text
[ Incoming Telemetry Alert ]
             │
             ▼
┌───────────────────────────┐
│   FastAPI Ingestion API   │ <── Pydantic V2 Request Validation
└────────────┬──────────────┘
             │
             ▼
┌───────────────────────────┐
│   Deduplication Service   │ <── SHA-256 Fingerprinting O(1)
└────────────┬──────────────┘
             │
      ┌──────┴────────────────────────┐
      │                               │
 [Exact Match Found]        [New Unique Incident]
      │                               │
      ▼                               ▼
 Link to Existing           1. SentenceTransformers (384-dim Vector)
 Incident Record            2. PostgreSQL pgvector (HNSW Index Search)
                            3. Async LLM Root-Cause Analysis Worker