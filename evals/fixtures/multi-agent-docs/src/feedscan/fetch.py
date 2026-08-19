"""Feed retrieval. One shared client, because the feeds live on three hosts."""

from __future__ import annotations

import httpx

TIMEOUT = httpx.Timeout(10.0, connect=5.0)
USER_AGENT = "feedscan/0.4.2 (+https://example.invalid/feedscan)"


def fetch(url: str, client: httpx.Client | None = None) -> bytes:
    owned = client is None
    client = client or httpx.Client(timeout=TIMEOUT, headers={"user-agent": USER_AGENT})
    try:
        response = client.get(url, follow_redirects=True)
        response.raise_for_status()
        return response.content
    finally:
        if owned:
            client.close()
