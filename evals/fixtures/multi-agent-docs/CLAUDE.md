# CLAUDE.md

feedscan polls a handful of RSS feeds and keeps the entries in SQLite.

## Commands

- `make install` — `uv sync`, installs from the lockfile
- `make test` — pytest
- `make lint` / `make fmt` — ruff
- `make scan` — poll every feed once

Python 3.12 or newer. The project moved to `uv` in 0.4.0.

## Project structure

```
src/feedscan/
  cli.py       argparse entry point, `feedscan scan` and `feedscan list`
  fetch.py     httpx, one shared client
  parse.py     RSS -> list of dicts
  store.py     SQLite, upsert on link
  legacy/      OPML import, not wired into the CLI
tests/         test_*.py, one per module
```

## Conventions

- Tests are named `test_*.py`, one file per module.
- Type hints everywhere; `from __future__ import annotations` at the top of
  every module so the 3.12 syntax stays readable.
- Anything that touches the network goes through `fetch.py`. Tests never hit
  the network.

## Gotchas

- **The parser is deliberately lenient about dates.** Three of the four feeds
  we poll ship malformed `<pubDate>` values. A date that will not parse becomes
  `None` and the entry is kept. Do not "fix" this by raising — it would drop
  most of the corpus. `test_parse.py` pins the behaviour.
- **`parse_feed` drops items with no `<link>` without saying so.** `link` is
  the primary key in `entries`, so an item without one cannot be stored. When a
  feed's item count and the row count disagree, this is almost always why.
- `link` is the natural key in `entries`, not an autoincrement id — feeds
  reissue the same item with a new title, and `ON CONFLICT DO NOTHING` is what
  keeps the first version.
- The SQLite file is disposable: delete it and re-scan if it ever misbehaves.
- `FEEDSCAN_DB` and `FEEDSCAN_FEEDS` are read at import time in `cli.py`, so a
  test that sets them with `monkeypatch.setenv` has to reload the module.

## General guidance

- Write clean, readable code
- Keep functions small and focused
- Handle errors properly
- Add tests for new functionality
