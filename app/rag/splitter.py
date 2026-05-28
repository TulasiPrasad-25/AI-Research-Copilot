from app.rag.loader import Document


def split_documents(documents: list[Document], chunk_size: int = 1200, chunk_overlap: int = 200) -> list[Document]:
    chunks: list[Document] = []
    step = max(1, chunk_size - chunk_overlap)

    for document in documents:
        text = " ".join((document.page_content or "").split())
        if not text:
            continue

        for start in range(0, len(text), step):
            chunk_text = text[start : start + chunk_size]
            if chunk_text:
                chunks.append(Document(page_content=chunk_text, metadata=dict(document.metadata)))

    return chunks
