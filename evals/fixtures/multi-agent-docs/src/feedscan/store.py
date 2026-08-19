"""SQLite persistence. `link` is the natural key — feeds reissue items."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    link      TEXT PRIMARY KEY,
    feed      TEXT NOT NULL,
    title     TEXT NOT NULL,
    published TEXT,
    seen_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS entries_feed ON entries (feed);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def upsert(conn: sqlite3.Connection, feed: str, entries: list[dict]) -> int:
    rows = [
        (e["link"], feed, e["title"], e["published"].isoformat() if e["published"] else None)
        for e in entries
    ]
    cur = conn.executemany(
        "INSERT INTO entries (link, feed, title, published) VALUES (?, ?, ?, ?) "
        "ON CONFLICT (link) DO NOTHING",
        rows,
    )
    conn.commit()
    return cur.rowcount
