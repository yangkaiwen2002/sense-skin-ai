"""
Mixed Chinese/English tokenizer for the BM25 retrieval leg.

Chinese text cannot be tokenized by whitespace-splitting (CS2 knowledge base
content is mostly unsegmented Chinese prose with embedded English terms like
"AK-47" or "Dragon Lore"). Both documents and queries MUST be tokenized with
this exact function so BM25's vocabulary lines up between indexing and
search time — using different tokenizers for the two would silently break
every match.
"""
from __future__ import annotations

import re

_EN_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
_CJK_RE = re.compile(r"[一-鿿]+")


def tokenize(text: str) -> list[str]:
    """
    Tokenize mixed CN/EN text for BM25.

    - English words / numbers are lowercased and kept as whole tokens,
      so "AK-47" -> ["ak", "47"] and matches both "ak47" and "AK-47" queries.
    - Contiguous Chinese runs are split into overlapping character bigrams
      (a lone trailing character keeps a unigram token), which gives BM25
      partial-substring recall similar to what the char n-gram TF-IDF
      retriever gets from sklearn's `char_wb` analyzer.
    """
    if not text:
        return []

    tokens: list[str] = [t.lower() for t in _EN_TOKEN_RE.findall(text)]

    for run in _CJK_RE.findall(text):
        if len(run) == 1:
            tokens.append(run)
        else:
            tokens.extend(run[i:i + 2] for i in range(len(run) - 1))

    return tokens
