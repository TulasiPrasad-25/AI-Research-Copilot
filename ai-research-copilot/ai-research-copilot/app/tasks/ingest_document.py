from app.tasks.worker import celery_app
from app.core.database import SessionLocal
from app.models.document import Document, DocumentStatus
from app.rag.loader import load_document
from app.rag.splitter import split_documents
from app.rag.vectorstore import add_documents
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, name="ingest_document")
def ingest_document(self, document_id: int, user_id: int):
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Document {document_id} not found")
            return

        # Mark as processing
        doc.status = DocumentStatus.PROCESSING
        db.commit()

        # Load → split → embed → store
        pages = load_document(doc.file_path, doc.file_type)
        chunks = split_documents(pages)

        # Attach metadata to each chunk
        for chunk in chunks:
            chunk.metadata["document_id"] = document_id
            chunk.metadata["document_title"] = doc.title
            chunk.metadata["user_id"] = user_id

        count = add_documents(user_id, chunks)

        # Mark as indexed
        doc.status = DocumentStatus.INDEXED
        doc.chunk_count = count
        db.commit()

        logger.info(f"Document {document_id} indexed: {count} chunks")
        return {"document_id": document_id, "chunks": count}

    except Exception as exc:
        logger.error(f"Failed to ingest document {document_id}: {exc}")
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(exc)
            db.commit()
        raise self.retry(exc=exc, countdown=10)

    finally:
        db.close()
