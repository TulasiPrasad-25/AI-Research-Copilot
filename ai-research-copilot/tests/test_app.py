import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db

TEST_DB = "sqlite:///./test.db"
engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200


def test_register_and_login():
    r = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "password123"
    })
    assert r.status_code == 201
    assert r.json()["email"] == "test@example.com"

    r = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "password123"
    })
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_duplicate_register():
    for _ in range(2):
        r = client.post("/api/auth/register", json={
            "email": "dup@example.com",
            "full_name": "Dup User",
            "password": "pass"
        })
    assert r.status_code == 400


def get_token():
    client.post("/api/auth/register", json={
        "email": "user@example.com",
        "full_name": "User",
        "password": "pass123"
    })
    r = client.post("/api/auth/login", data={"username": "user@example.com", "password": "pass123"})
    return r.json()["access_token"]


def test_me_endpoint():
    token = get_token()
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "user@example.com"


def test_create_chat_session():
    token = get_token()
    r = client.post("/api/chat/sessions", json={"title": "My Session"},
                    headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201
    assert r.json()["title"] == "My Session"


def test_list_documents_empty():
    token = get_token()
    r = client.get("/api/documents/", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["total"] == 0
