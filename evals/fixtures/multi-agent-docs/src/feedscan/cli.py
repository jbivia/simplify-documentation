from __future__ import annotations

import argparse
import os
from pathlib import Path

from .fetch import fetch
from .parse import parse_feed
from .store import connect, upsert

FEEDS_FILE = Path(os.environ.get("FEEDSCAN_FEEDS", "feeds.txt"))
DB_PATH = Path(os.environ.get("FEEDSCAN_DB", "./data/feedscan.db"))


def _feeds() -> list[str]:
    if not FEEDS_FILE.exists():
        return []
    return [l.strip() for l in FEEDS_FILE.read_text().splitlines() if l.strip() and l[0] != "#"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="feedscan")
    parser.add_argument("command", choices=["scan", "list"])
    args = parser.parse_args(argv)

    conn = connect(DB_PATH)
    if args.command == "scan":
        total = 0
        for url in _feeds():
            total += upsert(conn, url, parse_feed(fetch(url)))
        print(f"{total} new entries")
        return 0

    for row in conn.execute("SELECT feed, title FROM entries ORDER BY seen_at DESC LIMIT 20"):
        print(f"{row['feed']}  {row['title']}")
    return 0
