from app.rag.loader import Document
from app.rag.splitter import split_documents
from app.rag import vectorstore


def test_split_documents_preserves_metadata():
    docs = [Document(page_content="alpha beta gamma " * 200, metadata={"page": 2, "document_id": 10})]

    chunks = split_documents(docs, chunk_size=120, chunk_overlap=20)

    assert len(chunks) > 1
    assert chunks[0].metadata["page"] == 2
    assert chunks[0].metadata["document_id"] == 10
    assert chunks[0].metadata["page_chunk"] == 1


def test_vectorstore_search_and_remove(tmp_path, monkeypatch):
    monkeypatch.setattr(vectorstore, "INDEX_PATH", tmp_path)

    def fake_embed(texts):
        values = {
            "alpha research": [1.0, 0.0, 0.0],
            "beta methods": [0.0, 1.0, 0.0],
            "alpha question": [1.0, 0.0, 0.0],
        }
        return [values[text] for text in texts]

    monkeypatch.setattr(vectorstore, "embed_texts", fake_embed)

    chunks = [
        Document(page_content="alpha research", metadata={"document_id": 7, "document_title": "A"}),
        Document(page_content="beta methods", metadata={"document_id": 8, "document_title": "B"}),
    ]

    assert vectorstore.add_documents(1, chunks) == 2
    results = vectorstore.similarity_search(1, "alpha question", k=1)

    assert results[0].page_content == "alpha research"
    assert results[0].metadata["document_title"] == "A"

    assert vectorstore.remove_document(1, 7) == 1
    results = vectorstore.similarity_search(1, "alpha question", k=2)
    assert all(result.metadata["document_id"] != 7 for result in results)
