# legacy/

Dead weight, kept for one pending Feedly migration. Do not extend it.

- `opml.py` is not imported by the CLI. It exists so someone can call
  `feeds_from_opml()` by hand and paste the result into `feeds.txt`.
- No tests, deliberately. Once the migration is done this directory goes.
