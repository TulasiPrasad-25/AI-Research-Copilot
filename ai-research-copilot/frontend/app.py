import streamlit as st
import httpx
import os

API = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="AI Research Copilot", page_icon="🔬", layout="wide")

for key, val in {"token": None, "user": None, "session_id": None, "messages": []}.items():
    if key not in st.session_state:
        st.session_state[key] = val


def api(method, path, **kwargs):
    headers = kwargs.pop("headers", {})
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    try:
        r = getattr(httpx, method)(f"{API}{path}", headers=headers, timeout=30, **kwargs)
        return r
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def login_page():
    st.title("🔬 AI Research Copilot")
    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        with st.form("login"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                r = api("post", "/api/auth/login", data={"username": email, "password": password})
                if r and r.status_code == 200:
                    st.session_state.token = r.json()["access_token"]
                    me = api("get", "/api/auth/me")
                    if me:
                        st.session_state.user = me.json()
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    with tab2:
        with st.form("register"):
            full_name = st.text_input("Full Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Register"):
                r = api("post", "/api/auth/register", json={"full_name": full_name, "email": email, "password": password})
                if r and r.status_code == 201:
                    st.success("Account created! Please login.")
                else:
                    st.error(r.json().get("detail", "Error") if r else "Error")


def main_app():
    user = st.session_state.user
    with st.sidebar:
        st.markdown(f"**{user['full_name']}**")
        st.caption(user["email"])
        st.divider()
        st.subheader("📄 Upload Paper")
        file = st.file_uploader("PDF / TXT / DOCX", type=["pdf", "txt", "docx"])
        if file and st.button("Upload & Index"):
            with st.spinner("Uploading..."):
                r = api("post", "/api/documents/upload", files={"file": (file.name, file.getvalue(), file.type)})
                if r and r.status_code == 201:
                    st.success("Uploaded! Indexing in background...")
                else:
                    st.error("Upload failed")
        st.divider()
        st.subheader("📚 My Documents")
        r = api("get", "/api/documents/")
        if r and r.status_code == 200:
            for doc in r.json()["items"]:
                icon = {"indexed": "✅", "processing": "⏳", "pending": "🕐", "failed": "❌"}.get(doc["status"], "❓")
                c1, c2 = st.columns([4, 1])
                c1.caption(f"{icon} {doc['title'][:30]}")
                if c2.button("🗑", key=f"del_{doc['id']}"):
                    api("delete", f"/api/documents/{doc['id']}")
                    st.rerun()
        st.divider()
        st.subheader("💬 Chats")
        if st.button("+ New Chat"):
            r = api("post", "/api/chat/sessions", json={"title": "New Chat"})
            if r and r.status_code == 201:
                st.session_state.session_id = r.json()["id"]
                st.session_state.messages = []
                st.rerun()
        r = api("get", "/api/chat/sessions")
        if r and r.status_code == 200:
            for s in r.json():
                label = f"{'▶ ' if s['id'] == st.session_state.session_id else ''}{s['title'][:28]}"
                if st.button(label, key=f"s_{s['id']}"):
                    st.session_state.session_id = s["id"]
                    msgs = api("get", f"/api/chat/sessions/{s['id']}/messages")
                    st.session_state.messages = msgs.json() if msgs and msgs.status_code == 200 else []
                    st.rerun()
        st.divider()
        if st.button("Logout"):
            for k in ["token", "user", "session_id", "messages"]:
                st.session_state[k] = None if k != "messages" else []
            st.rerun()

    st.title("🔬 AI Research Copilot")
    if not st.session_state.session_id:
        st.info("Create or select a chat from the sidebar.")
        return

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("📎 Sources"):
                    for src in msg["sources"]:
                        st.caption(f"**{src.get('document_title','Unknown')}** — page {src.get('page','?')}")
                        st.markdown(f"> {src.get('content','')[:300]}...")

    if prompt := st.chat_input("Ask about your research papers..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                r = api("post", "/api/chat/ask", json={"question": prompt, "session_id": st.session_state.session_id})
                if r and r.status_code == 200:
                    reply = r.json()
                    st.markdown(reply["content"])
                    if reply.get("sources"):
                        with st.expander("📎 Sources"):
                            for src in reply["sources"]:
                                st.caption(f"**{src.get('document_title','Unknown')}**")
                                st.markdown(f"> {src.get('content','')[:300]}...")
                    st.session_state.messages.append(reply)
                else:
                    st.error("Failed to get response")


if st.session_state.token:
    main_app()
else:
    login_page()
