# 🔬 AI Research Copilot

RAG-powered research assistant. Upload papers → ask questions → get cited answers.

## Stack
| Layer | Tech |
|-------|------|
| API | FastAPI + Uvicorn |
| Auth | JWT (access + refresh tokens) |
| DB | PostgreSQL + SQLAlchemy + Alembic |
| Cache / Broker | Redis |
| Async Indexing | Celery |
| RAG | LangChain + FAISS + OpenAI GPT-4o |
| Frontend | Streamlit |
| DevOps | Docker Compose + GitHub Actions |

## Quick Start

```bash
# 1. Clone
git clone <your-repo>
cd ai-research-copilot

# 2. Set env
cp .env.example .env
# → Add OPENAI_API_KEY and change secret keys

# 3. Run
docker-compose up --build

# API docs  → http://localhost:8000/docs
# Frontend  → http://localhost:8501
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/auth/register | Register |
| POST | /api/auth/login | Login → JWT |
| POST | /api/auth/refresh | Refresh token |
| GET  | /api/auth/me | Current user |
| POST | /api/documents/upload | Upload + index paper |
| GET  | /api/documents/ | List documents |
| DELETE | /api/documents/{id} | Delete document |
| POST | /api/chat/sessions | Create chat session |
| GET  | /api/chat/sessions | List sessions |
| GET  | /api/chat/sessions/{id}/messages | Chat history |
| POST | /api/chat/ask | Ask a question (RAG) |

## Project Structure
```
app/
├── api/          # auth, documents, chat, users
├── core/         # config, database, redis, security, deps
├── models/       # SQLAlchemy: User, Document, ChatSession, ChatMessage
├── schemas/      # Pydantic schemas
├── services/     # auth_service, document_service, chat_service
├── tasks/        # Celery: ingest_document
└── rag/          # loader, splitter, vectorstore, pipeline
frontend/         # Streamlit UI
migrations/       # Alembic
tests/            # Pytest
```

## How It Works
1. User uploads a PDF/TXT/DOCX → saved to disk → Celery task fires
2. Celery loads → splits → embeds → stores in FAISS (per-user index)
3. User asks a question → FAISS similarity search → top 5 chunks → GPT-4o → answer with citations
4. All chat history saved in PostgreSQL per session
