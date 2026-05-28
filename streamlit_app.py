import io
import os
from contextlib import contextmanager
from types import SimpleNamespace

import streamlit as st

st.set_page_config(page_title="AI Research Copilot", page_icon="AI", layout="wide")

try:
    streamlit_secrets = dict(st.secrets)
except Exception:
    streamlit_secrets = {}

for secret_name in ("OPENAI_API_KEY", "DATABASE_URL", "JWT_SECRET_KEY", "FAISS_INDEX_PATH"):
    if secret_name in streamlit_secrets and not os.getenv(secret_name):
        os.environ[secret_name] = str(streamlit_secrets[secret_name])

os.environ.setdefault("DATABASE_URL", "sqlite:///./research_copilot.db")
os.environ.setdefault("JWT_SECRET_KEY", "change-me-for-production")
os.environ.setdefault("FAISS_INDEX_PATH", "./faiss_index")

import app.models  # noqa: E402,F401
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models.document import DocumentStatus  # noqa: E402
from app.rag.pipeline import run_rag_pipeline  # noqa: E402
from app.schemas.user import UserCreate  # noqa: E402
from app.services import chat_service  # noqa: E402
from app.services.auth_service import login_user, register_user  # noqa: E402
from app.services.document_service import delete_document, get_user_documents, save_upload  # noqa: E402
from app.services.ingestion_service import ingest_document_sync  # noqa: E402

Base.metadata.create_all(bind=engine)

DEFAULT_SESSION_STATE = {
    "user_id": None,
    "user": None,
    "session_id": None,
    "messages": [],
}

for key, value in DEFAULT_SESSION_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value.copy() if isinstance(value, list) else value


@contextmanager
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def current_user(db):
    if not st.session_state.user_id:
        return None
    return db.query(app.models.User).filter(app.models.User.id == st.session_state.user_id).first()


def show_error(prefix, exc):
    detail = getattr(exc, "detail", None)
    st.error(f"{prefix}: {detail or exc}")


def auth_page():
    st.title("AI Research Copilot")
    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", type="primary")

        if submitted:
            with db_session() as db:
                try:
                    login_user(db, email, password)
                    user = db.query(app.models.User).filter(app.models.User.email == email).first()
                    if not user:
                        raise ValueError("User was not found after login.")
                    st.session_state.user_id = user.id
                    st.session_state.user = {"email": user.email, "full_name": user.full_name}
                    st.rerun()
                except Exception as exc:
                    show_error("Login failed", exc)

    with register_tab:
        with st.form("register_form"):
            full_name = st.text_input("Full name")
            email = st.text_input("Email", key="register_email")
            password = st.text_input("Password", type="password", key="register_password")
            submitted = st.form_submit_button("Create account", type="primary")

        if submitted:
            with db_session() as db:
                try:
                    register_user(db, UserCreate(full_name=full_name, email=email, password=password))
                    st.success("Account created. You can log in now.")
                except Exception as exc:
                    show_error("Registration failed", exc)


def load_messages(db, session_id):
    messages = chat_service.get_session_messages(db, session_id, st.session_state.user_id)
    st.session_state.messages = [
        {
            "role": message.role,
            "content": message.content,
            "sources": message.sources or [],
        }
        for message in messages
    ]


def reset_login_state():
    for key, value in DEFAULT_SESSION_STATE.items():
        st.session_state[key] = value.copy() if isinstance(value, list) else value


def sidebar(db, user):
    with st.sidebar:
        st.markdown(f"**{user.full_name}**")
        st.caption(user.email)

        if not os.getenv("OPENAI_API_KEY"):
            st.warning("Add OPENAI_API_KEY in Streamlit secrets before indexing documents.")

        st.divider()
        st.subheader("Upload Paper")
        upload = st.file_uploader("PDF, TXT, or DOCX", type=["pdf", "txt", "docx"])
        if upload and st.button("Upload & Index", type="primary"):
            file = SimpleNamespace(filename=upload.name, file=io.BytesIO(upload.getvalue()))
            try:
                doc = save_upload(db, file, user.id)
                with st.spinner("Indexing document..."):
                    ingest_document_sync(doc.id, user.id)
                st.success("Document indexed.")
                st.rerun()
            except Exception as exc:
                show_error("Upload failed", exc)

        st.divider()
        st.subheader("Documents")
        for doc in get_user_documents(db, user.id):
            status_icon = {
                DocumentStatus.INDEXED: "OK",
                DocumentStatus.PROCESSING: "...",
                DocumentStatus.PENDING: "-",
                DocumentStatus.FAILED: "!",
            }.get(doc.status, "?")
            left, right = st.columns([5, 1])
            left.caption(f"{status_icon} {doc.title[:36]}")
            if right.button("Delete", key=f"delete_doc_{doc.id}"):
                delete_document(db, doc.id, user.id)
                st.rerun()
            if doc.error_message:
                st.caption(doc.error_message)

        st.divider()
        st.subheader("Chats")
        if st.button("New Chat"):
            session = chat_service.create_session(db, user.id, "New Chat")
            st.session_state.session_id = session.id
            st.session_state.messages = []
            st.rerun()

        for session in chat_service.get_user_sessions(db, user.id):
            label = session.title[:32]
            if session.id == st.session_state.session_id:
                label = f"> {label}"
            if st.button(label, key=f"session_{session.id}"):
                st.session_state.session_id = session.id
                load_messages(db, session.id)
                st.rerun()

        st.divider()
        if st.button("Logout"):
            reset_login_state()
            st.rerun()


def render_messages():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                with st.expander("Sources"):
                    for source in message["sources"]:
                        st.caption(f"{source.get('document_title', 'Unknown')} page {source.get('page', '?')}")
                        st.markdown(f"> {source.get('content', '')[:300]}...")


def app_page():
    with db_session() as db:
        user = current_user(db)
        if not user:
            reset_login_state()
            st.rerun()

        sidebar(db, user)

        st.title("AI Research Copilot")
        if not st.session_state.session_id:
            st.info("Create or select a chat from the sidebar.")
            return

        if not st.session_state.messages:
            load_messages(db, st.session_state.session_id)

        render_messages()

        prompt = st.chat_input("Ask about your research papers...")
        if prompt:
            chat_service.save_message(db, st.session_state.session_id, "user", prompt)
            st.session_state.messages.append({"role": "user", "content": prompt, "sources": []})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    with st.spinner("Thinking..."):
                        result = run_rag_pipeline(user.id, prompt)
                    reply = chat_service.save_message(
                        db,
                        st.session_state.session_id,
                        "assistant",
                        result["answer"],
                        result["sources"],
                    )
                    st.markdown(reply.content)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": reply.content, "sources": reply.sources or []}
                    )
                except Exception as exc:
                    show_error("Question failed", exc)


if st.session_state.user_id:
    app_page()
else:
    auth_page()
