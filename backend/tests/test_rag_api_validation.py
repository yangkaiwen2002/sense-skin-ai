"""
API-level validation tests for POST /api/rag/query.

These only exercise request validation paths that run BEFORE the retriever
singleton or the Anthropic client are touched, so they need no network
access, no CLAUDE_API_KEY, and never download the embedding model:
  - empty question -> the router's own explicit check raises 400
  - out-of-range top_k -> Pydantic Field validation raises 422
Both checks happen ahead of `get_retriever()` in app/routers/rag.py.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_empty_question_returns_400():
    resp = client.post("/api/rag/query", json={"question": "   "})
    assert resp.status_code == 400
    assert "问题不能为空" in resp.json()["detail"]


def test_top_k_above_max_returns_422():
    resp = client.post("/api/rag/query", json={"question": "test", "top_k": 999})
    assert resp.status_code == 422


def test_top_k_below_min_returns_422():
    resp = client.post("/api/rag/query", json={"question": "test", "top_k": 0})
    assert resp.status_code == 422


def test_missing_question_field_returns_422():
    resp = client.post("/api/rag/query", json={})
    assert resp.status_code == 422
