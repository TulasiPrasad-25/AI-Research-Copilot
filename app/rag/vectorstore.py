import json
import math
import os
import re
import time
from pathlib import Path
from uuid import uuid4

import httpx

from app.core.config import settings
from app.rag.loader import Document

INDEX_PATH = Path(settings.FAISS_INDEX_PATH)
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_BATCH_SIZE = 64
MMR_LAMBDA = 0.72


def require_api_key() -> str:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is required to index and search documents.")
    return settings.OPENAI_API_KEY


def get_index_path(user_id: int) -> Path:
    path = INDEX_PATH / str(user_id)
    path.mkdir(parents=True, exist_ok=True)
    return path / "chunks.json"


def normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if not norm:
        return vector
    return [value / norm for value in vector]


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    api_key = require_api_key()
    embeddings: list[list[float]] = []

    for start in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[start : start + EMBEDDING_BATCH_SIZE]
        response = httpx.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": EMBEDDING_MODEL, "input": batch},
            timeout=90,
        )
        response.raise_for_status()
        data = response.json()["data"]
        embeddings.extend(normalize(item["embedding"]) for item in sorted(data, key=lambda item: item["index"]))

    return embeddings


def load_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_records(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(records, file)


def remove_document(user_id: int, document_id: int) -> int:
    path = get_index_path(user_id)
    records = load_records(path)
    kept = [record for record in records if record.get("metadata", {}).get("document_id") != document_id]
    save_records(path, kept)
    return len(records) - len(kept)


def add_documents(user_id: int, chunks: list[Document]) -> int:
    path = get_index_path(user_id)
    records = load_records(path)
    if chunks and "document_id" in chunks[0].metadata:
        document_id = chunks[0].metadata["document_id"]
        records = [record for record in records if record.get("metadata", {}).get("document_id") != document_id]

    texts = [chunk.page_content for chunk in chunks]
    embeddings = embed_texts(texts)

    for chunk_index, (chunk, embedding) in enumerate(zip(chunks, embeddings), start=1):
        metadata = dict(chunk.metadata)
        metadata["chunk_index"] = chunk_index
        records.append(
            {
                "id": str(uuid4()),
                "content": chunk.page_content,
                "metadata": metadata,
                "embedding": embedding,
                "created_at": int(time.time()),
            }
        )

    save_records(path, records)
    return len(chunks)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-zA-Z0-9]{3,}", text.lower())}


def lexical_score(query: str, content: str) -> float:
    query_tokens = tokenize(query)
    if not query_tokens:
        return 0.0
    content_tokens = tokenize(content)
    return len(query_tokens & content_tokens) / len(query_tokens)


def mmr_select(candidates: list[dict], k: int) -> list[dict]:
    selected: list[dict] = []
    remaining = candidates[:]

    while remaining and len(selected) < k:
        if not selected:
            selected.append(remaining.pop(0))
            continue

        def mmr_score(record: dict) -> float:
            diversity_penalty = max(
                cosine_similarity(record["embedding"], chosen["embedding"])
                for chosen in selected
            )
            return MMR_LAMBDA * record["score"] - (1 - MMR_LAMBDA) * diversity_penalty

        best = max(remaining, key=mmr_score)
        remaining.remove(best)
        selected.append(best)

    return selected


def similarity_search(user_id: int, query: str, k: int = 6, fetch_k: int = 18) -> list[Document]:
    path = get_index_path(user_id)
    records = load_records(path)
    if not records:
        return []

    query_embedding = normalize(embed_texts([query])[0])
    scored = []
    for record in records:
        semantic = cosine_similarity(query_embedding, record["embedding"])
        lexical = lexical_score(query, record["content"])
        scored.append({**record, "score": (0.86 * semantic) + (0.14 * lexical)})

    ranked = sorted(scored, key=lambda record: record["score"], reverse=True)[:fetch_k]
    selected = mmr_select(ranked, k)

    return [
        Document(page_content=record["content"], metadata={**record.get("metadata", {}), "score": record["score"]})
        for record in selected
    ]


def delete_user_index(user_id: int):
    path = get_index_path(user_id)
    if path.exists():
        os.remove(path)
