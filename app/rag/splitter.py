from app.rag.loader import Document


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    text = " ".join((text or "").split())
    if not text:
        return []

    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    if not paragraphs:
        paragraphs = [text]

    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        pieces = [paragraph]
        if len(paragraph) > chunk_size:
            pieces = []
            start = 0
            step = max(1, chunk_size - chunk_overlap)
            while start < len(paragraph):
                pieces.append(paragraph[start : start + chunk_size])
                start += step

        for piece in pieces:
            if not current:
                current = piece
            elif len(current) + len(piece) + 2 <= chunk_size:
                current = f"{current}\n\n{piece}"
            else:
                chunks.append(current)
                overlap = current[-chunk_overlap:] if chunk_overlap > 0 else ""
                current = f"{overlap} {piece}".strip()

    if current:
        chunks.append(current)

    return chunks


def split_documents(documents: list[Document], chunk_size: int = 1400, chunk_overlap: int = 220) -> list[Document]:
    chunks: list[Document] = []

    for document in documents:
        for index, chunk_text in enumerate(split_text(document.page_content, chunk_size, chunk_overlap)):
            metadata = dict(document.metadata)
            metadata["page_chunk"] = index + 1
            chunks.append(Document(page_content=chunk_text, metadata=metadata))

    return chunks
