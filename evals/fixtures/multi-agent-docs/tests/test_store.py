from feedscan.store import connect, upsert


def test_upsert_is_idempotent_on_link(tmp_path):
    conn = connect(tmp_path / "db.sqlite")
    entries = [{"link": "https://a.invalid/1", "title": "Un", "published": None}]
    assert upsert(conn, "feed-a", entries) == 1
    assert upsert(conn, "feed-a", entries) == 0


def test_rows_come_back_in_insertion_order(tmp_path):
    conn = connect(tmp_path / "db.sqlite")
    upsert(conn, "f", [{"link": f"https://a.invalid/{i}", "title": str(i), "published": None}
                       for i in range(3)])
    titles = [r["title"] for r in conn.execute("SELECT title FROM entries")]
    assert titles == ["0", "1", "2"]
