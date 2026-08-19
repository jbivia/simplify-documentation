"""OPML import, kept for the one user who still has a Feedly export.

Not wired into the CLI. Slated for removal once that import is done.
"""

from __future__ import annotations

from defusedxml import ElementTree


def feeds_from_opml(payload: bytes) -> list[str]:
    root = ElementTree.fromstring(payload)
    return [o.get("xmlUrl") for o in root.iter("outline") if o.get("xmlUrl")]
