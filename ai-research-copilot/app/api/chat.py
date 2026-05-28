from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.chat import ChatSessionCreate, ChatSessionOut, ChatMessageIn, ChatMessageOut
from app.services import chat_service
from app.rag.pipeline import run_rag_pipeline

router = APIRouter()


@router.post("/sessions", response_model=ChatSessionOut, status_code=201)
def create_session(
    data: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return chat_service.create_session(db, current_user.id, data.title)


@router.get("/sessions", response_model=list[ChatSessionOut])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return chat_service.get_user_sessions(db, current_user.id)


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageOut])
def get_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return chat_service.get_session_messages(db, session_id, current_user.id)


@router.post("/ask", response_model=ChatMessageOut)
def ask(
    data: ChatMessageIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate session belongs to user
    chat_service.get_session(db, data.session_id, current_user.id)

    # Save user message
    chat_service.save_message(db, data.session_id, "user", data.question)

    # Run RAG pipeline
    result = run_rag_pipeline(current_user.id, data.question)

    # Save assistant reply with sources
    reply = chat_service.save_message(
        db, data.session_id, "assistant", result["answer"], result["sources"]
    )
    return reply


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat_service.delete_session(db, session_id, current_user.id)
