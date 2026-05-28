<div align="center">

#  AI Research Copilot

**RAG-powered research assistant — Ingest documents, ask questions, get cited answers.**

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat&logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.3-37814A?style=flat&logo=celery&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.2-1C3C3C?style=flat)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=flat&logo=openai&logoColor=white)

</div>

---

##  What It Does

Upload research papers (PDF, DOCX, TXT) → they get chunked and embedded in the background → ask natural language questions → get accurate answers with source citations pulled directly from your documents.

Built as a full production-grade backend, not a notebook prototype.

---

##  Architecture

```
Streamlit UI
     │
     ▼
FastAPI  ──── JWT Auth
     │
     ├──── PostgreSQL  (users, documents, chat history)
     │
     ├──── Redis  (broker + cache)
     │
     └──── Celery Worker
                │
                ▼
          RAG Pipeline (LangChain)
          ┌─────────────────────┐
          │ Load → Split →      │
          │ Embed → FAISS Index │
          └─────────────────────┘
                │
                ▼
          OpenAI GPT-4o  →  Answer + Citations
```

---

##  Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI + Uvicorn |
| Auth | JWT — access + refresh tokens (python-jose + bcrypt) |
| Database | PostgreSQL + SQLAlchemy ORM |
| Cache / Broker | Redis |
| Async Indexing | Celery background workers |
| RAG | LangChain + FAISS + OpenAI Embeddings |
| LLM | OpenAI GPT-4o |
| Frontend | Streamlit |
| Containerization | Docker + Docker Compose (6 services) |
| CI/CD | GitHub Actions |

---

##  Quick Start

### Prerequisites
- Docker Desktop
- OpenAI API key

### Run

```bash
# 1. Clone
git clone https://github.com/TulasiPrasad-25/ai-research-copilot.git
cd ai-research-copilot

# 2. Configure
cp .env.example .env
# Add your OPENAI_API_KEY in .env

# 3. Start
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Streamlit UI | http://localhost:8501 |
| API Swagger docs | http://localhost:8000/docs |

---

##  Project Structure

```
app/
├── api/            # Route handlers — auth, documents, chat, users
├── core/           # Config, database, Redis, JWT security, dependencies
├── models/         # SQLAlchemy — User, Document, ChatSession, ChatMessage
├── schemas/        # Pydantic request/response schemas
├── services/       # Business logic — auth, document, chat
├── tasks/          # Celery async tasks — document ingestion + indexing
└── rag/            # LangChain pipeline — loader, splitter, vectorstore, pipeline
frontend/           # Streamlit multi-page UI
migrations/         # Alembic database migrations
tests/              # Pytest test suite
```

---

##  API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login → JWT tokens |
| POST | `/api/auth/refresh` | Refresh access token |
| GET | `/api/auth/me` | Get current user |
| POST | `/api/documents/upload` | Upload + trigger indexing |
| GET | `/api/documents/` | List user's documents |
| DELETE | `/api/documents/{id}` | Delete document |
| POST | `/api/chat/sessions` | Create chat session |
| GET | `/api/chat/sessions` | List sessions |
| GET | `/api/chat/sessions/{id}/messages` | Chat history |
| POST | `/api/chat/ask` | Ask question → RAG answer |

---

##  How RAG Works

1. User uploads a PDF → saved to disk → Celery task fires immediately
2. Celery loads the file → splits into chunks (1000 tokens, 200 overlap)
3. Each chunk is embedded via OpenAI Embeddings → stored in FAISS (per-user index)
4. On question → top 5 relevant chunks retrieved → passed to GPT-4o with prompt
5. Answer returned with source citations → saved to PostgreSQL chat history

---

##  Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

---

##  Author

**Tulasi Prasad** — B.Tech CSE (AI & Data Science)

[![GitHub](https://img.shields.io/badge/GitHub-TulasiPrasad--25-181717?style=flat&logo=github)](https://github.com/TulasiPrasad-25)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-tulasi--prasad-0A66C2?style=flat&logo=linkedin)](https://linkedin.com/in/tulasi-prasad-077350284)
[![Portfolio](https://img.shields.io/badge/Portfolio-TulasiPrasad--25.github.io-000000?style=flat)](https://TulasiPrasad-25.github.io)
