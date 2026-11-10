# Personal Health Assistant

A privacy-first, zero-retention symptom assessment and health triage assistant. Designed for users needing quick clinical guidance at home or when away from a healthcare provider. Users complete an ultra-fast onboarding (Name, Age, Sex), describe their symptoms, answer conversational follow-up questions (medications, allergies, pregnancy status if female), and can optionally attach medical documents (PDF) for direct in-context analysis.

If critical or life-threatening symptoms are detected, the system immediately presents an emergency alert with a one-touch call button (`tel:911`), followed by nearby 24/7 emergency facilities using the free OpenStreetMap Overpass API.

---

## Key Architectural Principles

- **Zero-Retention Privacy**: No permanent database. Patient profiles, conversations, and document text live strictly in volatile memory with rolling 30-minute TTLs and are purged upon session end or inactivity.
- **Deterministic-First Safety**: A deterministic red-flag rule engine executes on *every user turn* before any LLM call, guaranteeing zero-latency emergency escalation independent of model availability or rate limits.
- **Post-LLM Escalation Floor**: The LLM outputs structured JSON. A post-LLM validator enforces an escalation floor (triage severity can be raised, never lowered) and strictly rejects medication-stopping directives or dosing adjustments.
- **In-Memory Direct Context**: PDFs are parsed in-memory from byte streams (zero `/tmp` disk writes) and injected directly into Gemini 2.5 Flash's 1M context window. This preserves complete lab tables, units, and reference ranges without chunking artifacts.
- **Free External Providers**: Uses Google Gemini (Free tier) and OpenStreetMap Overpass API (Free/Open).

---

## Tech Stack

- **API Framework**: FastAPI (Python 3.12), Pydantic v2
- **LLM**: Google Gemini 2.5 Flash (`google-genai` SDK) with structured JSON output
- **PDF Extraction**: PyMuPDF (`fitz`) from in-memory byte streams
- **Emergency Geolocation**: OpenStreetMap Overpass API (Free 24/7 ER/hospital locator)
- **Containerization**: Docker & Docker Compose (single stateless API container)

---

## Running Locally with Docker

1. Copy `.env.example` to `backend/.env` and set your `GEMINI_API_KEY`:
   ```bash
   cp backend/.env.example backend/.env
   ```

2. Start the service:
   ```bash
   docker compose up --build
   ```

3. The API will be live at `http://localhost:8000`. Interactive docs are available at `http://localhost:8000/docs`.

---

## API Endpoints (`/api/v1`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/session/start` | Rapid guest onboarding (Name, Age, Sex). Sets `HttpOnly` session cookie. |
| `POST` | `/api/v1/session/end` | Explicitly wipes session state from memory and clears session cookie. |
| `POST` | `/api/v1/chat` | Evaluates symptoms, runs red-flag checks, and returns structured triage. |
| `POST` | `/api/v1/documents/upload` | In-memory upload of optional medical PDF (max 10MB, max 10 pages). |
| `GET` | `/api/v1/emergency/facilities` | Asynchronously locates nearby 24/7 ERs via OpenStreetMap (`lat`, `lon`). |
| `GET` | `/api/v1/health` | Service health status. |

---

## Documentation

- [User Stories Specification](docs/user_stories.md)
- [System Architecture Specification](docs/architecture.md)