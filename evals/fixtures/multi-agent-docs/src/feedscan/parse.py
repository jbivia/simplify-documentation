"""RSS parsing.

Deliberately lenient about dates: three of the four feeds we poll ship
malformed <pubDate> values, so a date that will not parse becomes None and the
entry is kept. Raising here would drop most of the corpus.
"""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from defusedxml import ElementTree


def _parse_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def parse_feed(payload: bytes) -> list[dict]:
    root = ElementTree.fromstring(payload)
    entries = []
    for item in root.iter("item"):
        link = item.findtext("link")
        if not link:
            continue
        entries.append(
            {
                "link": link.strip(),
                "title": (item.findtext("title") or "").strip(),
                "published": _parse_date(item.findtext("pubDate")),
            }
        )
    return entries
