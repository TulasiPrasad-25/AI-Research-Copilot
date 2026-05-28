# AI Research Copilot

RAG-powered research assistant. Upload papers, ask questions, and get answers with cited source snippets.

## Stack

| Layer | Tech |
| --- | --- |
| Streamlit app | Streamlit + SQLite + FAISS |
| Optional API | FastAPI + Uvicorn |
| Auth | JWT/password hashing |
| RAG | LangChain + FAISS + OpenAI |
| Optional async services | PostgreSQL + Redis + Celery via Docker Compose |

## Run Locally With Streamlit

This is the easiest way to run the project and the correct mode for Streamlit Community Cloud.

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

Create `.streamlit/secrets.toml` locally, or add these values in Streamlit Cloud secrets:

```toml
OPENAI_API_KEY = "your-openai-api-key"
JWT_SECRET_KEY = "use-a-long-random-secret"
DATABASE_URL = "sqlite:///./research_copilot.db"
FAISS_INDEX_PATH = "./faiss_index"
```

Without `OPENAI_API_KEY`, login and chat setup still work, but document indexing and AI answers are disabled.

## Deploy To Streamlit Community Cloud

1. Push this repository to GitHub.
2. In Streamlit Community Cloud, choose the repo.
3. Set **Main file path** to:

```text
streamlit_app.py
```

4. Add the secrets shown above in the app's **Secrets** panel.
5. Deploy.

Streamlit Cloud runs one Streamlit process, so `streamlit_app.py` is intentionally self-contained. It does not depend on a separate FastAPI server, PostgreSQL, Redis, or Celery worker.

## Optional FastAPI Mode

The FastAPI backend still works for local API development:

```bash
python -m uvicorn app.main:app --reload
```

API docs will be available at `http://localhost:8000/docs`.

By default, uploads are indexed with FastAPI background tasks. To use Celery, set:

```env
USE_CELERY=True
```

and run Redis plus a Celery worker.

## Docker Compose

For the full multi-service stack:

```bash
cp .env.example .env
# edit .env and set OPENAI_API_KEY plus strong secrets
docker-compose up --build
```

## Tests

```bash
python -m pytest -q
```

## Project Structure

```text
app/
  api/          FastAPI routes
  core/         config, database, security
  models/       SQLAlchemy models
  rag/          loaders, splitters, FAISS, OpenAI pipeline
  services/     auth, document, and chat logic
  tasks/        sync/Celery document ingestion
frontend/       legacy API-driven Streamlit frontend
streamlit_app.py  Streamlit Cloud entrypoint
tests/          Pytest suite
```
