"""
Test bootstrap: make `app.*` importable regardless of how pytest is invoked
(some CI setups run `pytest` from repo root, others `pytest` from backend/).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Sequence

import numpy as np
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

REAL_KNOWLEDGE_PATH = BACKEND_DIR / "data" / "knowledge.json"


class FakeSemanticEmbedder:
    """Deterministic, network-free stand-in for SentenceTransformerEmbedder.

    Maps text to a small fixed "topic" vector space by keyword bucket, so
    tests can control which documents are semantically close without
    downloading a real embedding model. Vectors are L2-normalized, matching
    the real embedder's contract (so cosine similarity == inner product).
    """

    _TOPIC_KEYWORDS: dict[str, list[str]] = {
        "liquidity":  ["流动性", "变现速度", "变现能力", "交易量", "liquidity"],
        "rarity":     ["稀有度", "rarity", "违禁", "隐秘", "保密"],
        "rent":       ["租", "rent", "押金", "悠悠有品", "IGXE"],
        "tournament": ["赛事", "major", "锦标赛", "贴纸", "tournament", "Major"],
    }
    _TOPICS = list(_TOPIC_KEYWORDS)

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        vecs = np.zeros((len(texts), len(self._TOPICS)), dtype="float32")
        for row, text in enumerate(texts):
            for col, topic in enumerate(self._TOPICS):
                for kw in self._TOPIC_KEYWORDS[topic]:
                    if kw in text:
                        vecs[row, col] += 1.0
            norm = float(np.linalg.norm(vecs[row]))
            if norm > 0:
                vecs[row] /= norm
            else:
                vecs[row, -1] = 1.0  # deterministic fallback direction for unrelated text
        return vecs


class BrokenEmbedder:
    """Simulates a total embedding-backend failure (no network / model missing)."""

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        raise RuntimeError("simulated embedding backend failure (no network)")


SAMPLE_ENTRIES = [
    {"id": 101, "title": "皮肤流动性评估方法", "category": "market_mechanics",
     "content": "皮肤的流动性评估方法包括 BUFF 平台日均交易量和买卖价差，交易量越大流动性越好。"},
    {"id": 102, "title": "AK-47 红线市场特征", "category": "specific_skins",
     "content": "AK-47 | Redline 是流动性最好的皮肤之一，FT 版本价格约 300-450 元。"},
    {"id": 103, "title": "Major 赛事对皮肤价格的影响", "category": "tournament_effects",
     "content": "CS2 Major 赛事期间贴纸胶囊需求激增，价格通常在赛前两周上涨。"},
    {"id": 104, "title": "悠悠有品租赁费用详解", "category": "rent_vs_buy",
     "content": "悠悠有品租赁需缴纳押金，日租金约为皮肤估值的 0.6%-1.0%。"},
    {"id": 105, "title": "稀有度等级体系", "category": "rarity_guide",
     "content": "CS2 饰品稀有度从低到高分为消费级、工业级、军规级、受限级、保密级、隐秘级、违禁级。"},
]


@pytest.fixture
def sample_kb_path(tmp_path: Path) -> Path:
    path = tmp_path / "knowledge.json"
    path.write_text(json.dumps(SAMPLE_ENTRIES, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.fixture
def empty_kb_path(tmp_path: Path) -> Path:
    path = tmp_path / "knowledge.json"
    path.write_text("[]", encoding="utf-8")
    return path


@pytest.fixture
def single_entry_kb_path(tmp_path: Path) -> Path:
    path = tmp_path / "knowledge.json"
    path.write_text(json.dumps(SAMPLE_ENTRIES[:1], ensure_ascii=False), encoding="utf-8")
    return path


@pytest.fixture
def malformed_kb_path(tmp_path: Path) -> Path:
    path = tmp_path / "knowledge.json"
    path.write_text("{not valid json", encoding="utf-8")
    return path
