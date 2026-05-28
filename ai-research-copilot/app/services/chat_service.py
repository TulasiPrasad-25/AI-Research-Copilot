from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.chat import ChatSession, ChatMessage
from app.models.user import User


def create_session(db: Session, user_id: int, title: str = "New Chat") -> ChatSession:
    session = ChatSession(user_id=user_id, title=title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_user_sessions(db: Session, user_id: int) -> list[ChatSession]:
    return db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.created_at.desc()).all()


def get_session(db: Session, session_id: int, user_id: int) -> ChatSession:
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session


def get_session_messages(db: Session, session_id: int, user_id: int) -> list[ChatMessage]:
    get_session(db, session_id, user_id)
    return db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at).all()


def save_message(db: Session, session_id: int, role: str, content: str, sources: list = None) -> ChatMessage:
    msg = ChatMessage(session_id=session_id, role=role, content=content, sources=sources)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def delete_session(db: Session, session_id: int, user_id: int):
    session = get_session(db, session_id, user_id)
    db.delete(session)
    db.commit()
