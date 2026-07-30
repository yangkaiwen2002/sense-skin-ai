"""Unit tests for app/rag/tokenization.py — mixed CN/EN BM25 tokenizer."""
from __future__ import annotations

from app.rag.tokenization import tokenize


def test_tokenize_empty_string_returns_empty_list():
    assert tokenize("") == []
    assert tokenize(None) == []  # type: ignore[arg-type]


def test_tokenize_english_words_and_numbers_lowercased():
    assert tokenize("AK-47 skin investment") == ["ak", "47", "skin", "investment"]


def test_tokenize_chinese_produces_overlapping_bigrams():
    tokens = tokenize("流动性")
    assert tokens == ["流动", "动性"]


def test_tokenize_single_chinese_char_keeps_unigram():
    assert tokenize("刀") == ["刀"]


def test_query_and_document_tokenize_identically():
    """BM25 requires the exact same tokenizer at index time and query time."""
    doc = "皮肤的流动性评估方法"
    query = "流动性"
    doc_tokens = tokenize(doc)
    query_tokens = tokenize(query)
    assert all(t in doc_tokens for t in query_tokens)
