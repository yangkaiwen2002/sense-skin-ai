"""Additive upgrade for pre-provenance SQLite databases. No history is relabeled.

Run once during single-process startup. Larger deployments should move this
upgrade into their migration runner before starting multiple workers.
"""
from sqlalchemy import inspect, text


def ensure_price_provenance(engine):
    columns = {c["name"] for c in inspect(engine).get_columns("price_snapshots")}
    additions = {
        "source": "VARCHAR NOT NULL DEFAULT 'unknown'",
        "price_kind": "VARCHAR NOT NULL DEFAULT 'legacy_unknown'",
        "source_item_id": "VARCHAR",
    }
    with engine.begin() as conn:
        for name, definition in additions.items():
            if name not in columns:
                conn.execute(text(f"ALTER TABLE price_snapshots ADD COLUMN {name} {definition}"))
