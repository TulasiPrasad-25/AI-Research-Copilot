import json
import math
import os
from pathlib import Path

import httpx

from app.core.config import settings
from app.rag.loader import Document

INDEX_PATH = Path(settings.FAISS_INDEX_PATH)
EMBEDDING_MODEL = "text-embedding-3-small"


def require_api_key() -> str:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is required to index and search documents.")
    return settings.OPENAI_API_KEY


def get_index_path(user_id: int) -> Path:
    path = INDEX_PATH / str(user_id)
    path.mkdir(parents=True, exist_ok=True)
    return path / "chunks.json"


def embed_texts(texts: list[str]) -> list[list[float]]:
    api_key = require_api_key()
    response = httpx.post(
        "https://api.openai.com/v1/embeddings",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": EMBEDDING_MODEL, "input": texts},
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()["data"]
    return [item["embedding"] for item in sorted(data, key=lambda item: item["index"])]


def load_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_records(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(records, file)


def add_documents(user_id: int, chunks: list[Document]) -> int:
    path = get_index_path(user_id)
    records = load_records(path)
    texts = [chunk.page_content for chunk in chunks]
    embeddings = embed_texts(texts)

    for chunk, embedding in zip(chunks, embeddings):
        records.append(
            {
                "content": chunk.page_content,
                "metadata": chunk.metadata,
                "embedding": embedding,
            }
        )

    save_records(path, records)
    return len(chunks)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


def similarity_search(user_id: int, query: str, k: int = 5) -> list[Document]:
    path = get_index_path(user_id)
    records = load_records(path)
    if not records:
        return []

    query_embedding = embed_texts([query])[0]
    ranked = sorted(
        records,
        key=lambda record: cosine_similarity(query_embedding, record["embedding"]),
        reverse=True,
    )

    return [
        Document(page_content=record["content"], metadata=record.get("metadata", {}))
        for record in ranked[:k]
    ]


def delete_user_index(user_id: int):
    path = get_index_path(user_id)
    if path.exists():
        os.remove(path)
