from app.services.ingestion_service import ingest_document_sync
from app.tasks.worker import celery_app


@celery_app.task(bind=True, max_retries=3, name="ingest_document")
def ingest_document(self, document_id: int, user_id: int):
    try:
        return ingest_document_sync(document_id, user_id)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)
