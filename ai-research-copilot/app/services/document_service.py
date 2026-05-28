import os
import shutil
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from app.models.document import Document, DocumentStatus
from app.core.config import settings

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_TYPES = {"application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}


def save_upload(db: Session, file: UploadFile, user_id: int) -> Document:
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {ext} not supported. Use PDF, TXT, or DOCX.")

    file_path = os.path.join(UPLOAD_DIR, f"{user_id}_{file.filename}")
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    size = os.path.getsize(file_path)

    doc = Document(
        title=file.filename,
        filename=file.filename,
        file_path=file_path,
        file_type=ext.lstrip("."),
        file_size=size,
        status=DocumentStatus.PENDING,
        owner_id=user_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_user_documents(db: Session, user_id: int) -> list[Document]:
    return db.query(Document).filter(Document.owner_id == user_id).order_by(Document.created_at.desc()).all()


def get_document(db: Session, doc_id: int, user_id: int) -> Document:
    doc = db.query(Document).filter(Document.id == doc_id, Document.owner_id == user_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


def delete_document(db: Session, doc_id: int, user_id: int):
    doc = get_document(db, doc_id, user_id)
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    db.delete(doc)
    db.commit()
