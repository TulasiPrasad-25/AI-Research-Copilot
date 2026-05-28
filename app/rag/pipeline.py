import httpx

from app.core.config import settings
from app.rag.loader import Document
from app.rag.vectorstore import similarity_search

CHAT_MODEL = "gpt-4o-mini"
MAX_CONTEXT_CHARS = 9000


def require_api_key() -> str:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is required to answer questions.")
    return settings.OPENAI_API_KEY


def answer_question(context: str, question: str) -> str:
    api_key = require_api_key()
    response = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": CHAT_MODEL,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an AI research assistant using retrieval-augmented generation. "
                        "Answer only from the provided sources. If the answer is not supported, say so. "
                        "Cite evidence using the source labels like [S1] or [S2]."
                    ),
                },
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
            ],
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def run_rag_pipeline(user_id: int, question: str) -> dict:
    docs: list[Document] = similarity_search(user_id, question, k=6)

    if not docs:
        return {
            "answer": "No relevant documents found. Please upload research papers first.",
            "sources": [],
        }

    context_parts = []
    used_chars = 0
    for index, doc in enumerate(docs, start=1):
        meta = doc.metadata
        title = meta.get("document_title") or meta.get("source", "Unknown")
        page = meta.get("page")
        label = f"[S{index}] {title}"
        if page:
            label = f"{label}, page {page}"
        block = f"{label}\n{doc.page_content}"
        if used_chars + len(block) > MAX_CONTEXT_CHARS:
            break
        context_parts.append(block)
        used_chars += len(block)

    context = "\n\n".join(context_parts)
    answer = answer_question(context, question)

    sources = []
    for doc in docs:
        meta = doc.metadata
        sources.append(
            {
                "content": doc.page_content[:300],
                "document_title": meta.get("document_title") or meta.get("source", "Unknown"),
                "page": meta.get("page", None),
            }
        )

    return {
        "answer": answer,
        "sources": sources,
    }
