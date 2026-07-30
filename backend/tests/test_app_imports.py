"""Smoke test: the FastAPI app must import cleanly with no import-time errors,
and building it must not trigger network access (retriever/model loading is
lazy, only happening on the first real /api/rag/query request)."""
from __future__ import annotations


def test_app_imports_without_error():
    import app.main as main_module

    assert main_module.app.title == "SkinSense AI"


def test_rag_router_importable_without_touching_network():
    # Importing must not construct the singleton retriever (which would try
    # to download the embedding model) — get_retriever() is called lazily,
    # only inside the request handler.
    import app.rag.retriever as retriever_module

    assert retriever_module._retriever is None
