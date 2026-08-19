# AGENTS.md

feedscan is a small RSS poller that stores entries in SQLite.

## Setup

Install the dependencies with:

```bash
poetry install
```

Then run the test suite with `poetry run pytest`.

Requires Python 3.10 or newer.

## Layout

- `src/feedscan/cli.py` — command line entry point
- `src/feedscan/fetch.py` — HTTP
- `src/feedscan/parse.py` — RSS parsing
- `src/feedscan/store.py` — database
- `tests/` — the test suite

## Feeds

The list of feeds lives in `feeds.txt` at the repository root, one URL per
line. Lines starting with `#` are ignored. The path can be overridden with the
`FEEDSCAN_FEEDS` environment variable.

## Notes

- The date parser tolerates broken `pubDate` values rather than failing.
- Entries are keyed on their link.
- Never delete `data/feedscan.db`. It holds entries from feeds that have since
  gone offline; those cannot be fetched again.
- Please do not add dependencies without discussing it first.
