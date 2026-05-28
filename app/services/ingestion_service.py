import logging

from app.core.database import SessionLocal
from app.models.document import Document, DocumentStatus
from app.rag.loader import load_document
from app.rag.splitter import split_documents
from app.rag.vectorstore import add_documents

logger = logging.getLogger(__name__)


def ingest_document_sync(document_id: int, user_id: int):
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error("Document %s not found", document_id)
            return None

        doc.status = DocumentStatus.PROCESSING
        db.commit()

        pages = load_document(doc.file_path, doc.file_type)
        chunks = split_documents(pages)
        if not chunks:
            raise ValueError("No text could be extracted from this document.")

        for chunk in chunks:
            chunk.metadata["document_id"] = document_id
            chunk.metadata["document_title"] = doc.title
            chunk.metadata["user_id"] = user_id

        count = add_documents(user_id, chunks)

        doc.status = DocumentStatus.INDEXED
        doc.chunk_count = count
        doc.error_message = None
        db.commit()

        logger.info("Document %s indexed: %s chunks", document_id, count)
        return {"document_id": document_id, "chunks": count}

    except Exception as exc:
        logger.exception("Failed to ingest document %s", document_id)
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(exc)
            db.commit()
        raise

    finally:
        db.close()
