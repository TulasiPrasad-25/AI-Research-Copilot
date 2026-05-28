# AI Research Copilot

RAG-powered research assistant. Upload papers, ask questions, and get answers with cited source snippets.

## Run Locally With Streamlit

```bash
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

Create `.streamlit/secrets.toml` locally, or add the same values in Streamlit Cloud secrets:

```toml
OPENAI_API_KEY = "your-openai-api-key"
JWT_SECRET_KEY = "use-a-long-random-secret"
DATABASE_URL = "sqlite:///./research_copilot.db"
FAISS_INDEX_PATH = "./faiss_index"
```

Without `OPENAI_API_KEY`, login and chat setup work, but document indexing and AI answers are disabled.

## Deploy To Streamlit Community Cloud

Use these settings:

```text
Main file path: streamlit_app.py
Python runtime: python-3.11
```

If this project is inside a nested folder in your GitHub repo, use:

```text
Main file path: ai-research-copilot/streamlit_app.py
```

For nested repos, `runtime.txt` must still be in the GitHub repository root, not only inside the nested app folder.

## Required Files For Streamlit

```text
runtime.txt
requirements.txt
streamlit_app.py
app/
```

`runtime.txt` must contain:

```text
python-3.11
```

Do not commit `.streamlit/secrets.toml`.

## Optional FastAPI Mode

The FastAPI backend is still available for local API development:

```bash
python -m uvicorn app.main:app --reload
```

API docs will be available at `http://localhost:8000/docs`.

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
  rag/          document loaders, text splitter, JSON vector store, OpenAI HTTP pipeline
  services/     auth, document, chat, and ingestion logic
  tasks/        optional Celery task wrapper
frontend/       legacy API-driven Streamlit frontend
streamlit_app.py  Streamlit Cloud entrypoint
tests/          Pytest suite
```
