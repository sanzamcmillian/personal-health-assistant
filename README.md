# Personal Health Assistant

A minimal RAG (retrieval-augmented generation) backend: upload your own PDF
health documents, they get chunked and embedded, and you can then ask
questions answered only from the content of those documents, via Gemini.

This is a backend-only POC — there is no frontend yet.

## Stack

- FastAPI
- PostgreSQL + [pgvector](https://github.com/pgvector/pgvector) for embeddings
- SQLAlchemy 2.0 + Alembic
- Google Gemini (`google-genai`) for embeddings + generation
- PyMuPDF for PDF text extraction

## Running locally with Docker

1. Copy `backend/.env` and fill in `GEMINI_API_KEY` (get one from
   [Google AI Studio](https://aistudio.google.com/apikey)).
2. From the repo root:

   ```bash
   docker compose up --build
   ```

3. Run migrations (first time only, in another terminal):

   ```bash
   docker compose exec backend alembic upgrade head
   ```

4. The API is now live at `http://localhost:8000`. Interactive docs at
   `http://localhost:8000/docs`.

## API

- `GET /api/v1/health` — health check
- `POST /api/v1/documents/upload` — upload a PDF (multipart `file` field)
- `POST /api/v1/chat` — `{"question": "..."}`, answered using your uploaded
  documents as context, with `sources` pointing back to the originating
  document/chunk

## Running without Docker

```bash
cd backend
pip install -r requirements.txt
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/personal_health_assistant
export GEMINI_API_KEY=your-key-here
alembic upgrade head
uvicorn app.main:app --reload
```

## Notes / current limitations (POC scope)

- No auth — anyone with API access can upload/query documents.
- No chat session persistence yet (`ChatSession`/`Message` models exist but
  aren't wired into the chat endpoint) — each question is answered
  independently, with no conversation history.
- Local disk storage only (`backend/uploads/`); Google Cloud Storage is
  configured in `.env` but not yet implemented in `StorageService`.
- Chunking is fixed-size (800 chars, 150 overlap) per PDF page, not
  semantic/structure-aware.


## Future integrations

- Deploy on GCP
- implement github workflows
- add some frontend
- terraform