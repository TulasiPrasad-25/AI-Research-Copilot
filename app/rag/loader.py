from dataclasses import dataclass, field
from typing import Any

import docx2txt
from pypdf import PdfReader


@dataclass
class Document:
    page_content: str
    metadata: dict[str, Any] = field(default_factory=dict)


def load_document(file_path: str, file_type: str) -> list[Document]:
    if file_type == "pdf":
        reader = PdfReader(file_path)
        return [
            Document(page_content=page.extract_text() or "", metadata={"page": index + 1, "source": file_path})
            for index, page in enumerate(reader.pages)
        ]

    if file_type == "txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            return [Document(page_content=file.read(), metadata={"source": file_path})]

    if file_type == "docx":
        return [Document(page_content=docx2txt.process(file_path), metadata={"source": file_path})]

    raise ValueError(f"Unsupported file type: {file_type}")
