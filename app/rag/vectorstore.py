import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from typing import List
from app.core.config import settings

INDEX_PATH = settings.FAISS_INDEX_PATH


def get_embeddings() -> OpenAIEmbeddings:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is required to index and search documents.")
    return OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)


def get_index_path(user_id: int) -> str:
    path = os.path.join(INDEX_PATH, str(user_id))
    os.makedirs(path, exist_ok=True)
    return path


def add_documents(user_id: int, chunks: List[Document]) -> int:
    path = get_index_path(user_id)
    index_file = os.path.join(path, "index.faiss")
    embeddings = get_embeddings()

    if os.path.exists(index_file):
        store = FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
        store.add_documents(chunks)
    else:
        store = FAISS.from_documents(chunks, embeddings)

    store.save_local(path)
    return len(chunks)


def similarity_search(user_id: int, query: str, k: int = 5) -> List[Document]:
    path = get_index_path(user_id)
    index_file = os.path.join(path, "index.faiss")

    if not os.path.exists(index_file):
        return []

    embeddings = get_embeddings()
    store = FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
    return store.similarity_search(query, k=k)


def delete_user_index(user_id: int):
    import shutil
    path = get_index_path(user_id)
    if os.path.exists(path):
        shutil.rmtree(path)
