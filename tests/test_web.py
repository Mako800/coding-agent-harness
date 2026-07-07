import pytest
from harness.web import create_app

def test_health_endpoint():
    app = create_app(mock=True)
    client = app.test_client()
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json["status"] == "ok"

def test_index_page():
    app = create_app(mock=True)
    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Coding Agent Harness" in resp.data

def test_chat_mock_mode():
    app = create_app(mock=True)
    client = app.test_client()
    resp = client.post("/api/chat", json={"message": "hello"})
    assert resp.status_code == 200
    assert "mock mode" in resp.json["response"]

def test_chat_empty_message():
    app = create_app(mock=True)
    client = app.test_client()
    resp = client.post("/api/chat", json={"message": ""})
    assert resp.status_code == 400
