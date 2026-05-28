from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.document import DocumentOut, DocumentListOut
from app.services.document_service import save_upload, get_user_documents, get_document, delete_document
from app.tasks.ingest_document import ingest_document, ingest_document_sync
from app.core.config import settings

router = APIRouter()


@router.post("/upload", response_model=DocumentOut, status_code=201)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = save_upload(db, file, current_user.id)
    if settings.USE_CELERY:
        ingest_document.delay(doc.id, current_user.id)
    else:
        background_tasks.add_task(ingest_document_sync, doc.id, current_user.id)
    return doc


@router.get("/", response_model=DocumentListOut)
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    docs = get_user_documents(db, current_user.id)
    return {"total": len(docs), "items": docs}


@router.get("/{doc_id}", response_model=DocumentOut)
def get_doc(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_document(db, doc_id, current_user.id)


@router.delete("/{doc_id}", status_code=204)
def remove_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_document(db, doc_id, current_user.id)
