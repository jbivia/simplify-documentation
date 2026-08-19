from feedscan.parse import parse_feed

FEED = b"""<rss><channel>
  <item><title>Bon</title><link>https://a.invalid/1</link>
        <pubDate>Tue, 05 Aug 2025 09:00:00 +0000</pubDate></item>
  <item><title>Date cassee</title><link>https://a.invalid/2</link>
        <pubDate>hier soir</pubDate></item>
  <item><title>Sans lien</title></item>
</channel></rss>"""


def test_keeps_entries_with_unparseable_dates():
    entries = parse_feed(FEED)
    assert [e["title"] for e in entries] == ["Bon", "Date cassee"]
    assert entries[1]["published"] is None


def test_drops_entries_without_link():
    assert all(e["link"] for e in parse_feed(FEED))
