# Checking a documentation claim against the code

Both profiles need the same skill: taking a sentence from a doc and deciding whether the code agrees with it. This file is the lookup table.

## Three verdicts

**Confirmed** — the code says the same thing. Keep the claim (subject to the usual "is it worth its space" question).

**Contradicted** — the code says something else. Fix it or delete it. This is the highest-value finding in the whole pass; report these first.

**Unverifiable** — no trace either way in the repo. **This is not the same as false.** Infra constraints, team agreements, business rules, and lessons from past incidents all live outside the code. Report them in the uncertain bucket and let the user rule. Deleting these silently is how a cleanup destroys the only record of something that mattered.

## Where to check what

| Claim | Check |
|---|---|
| a command / script | `package.json` → `scripts`, `Makefile` targets, `pyproject.toml` → `[project.scripts]` / `[tool.poetry.scripts]`, `justfile`, `Taskfile.yml`, `composer.json`, CI workflow steps |
| a file or directory path | does it exist on disk right now |
| an environment variable | `process.env.X`, `import.meta.env.X`, `os.environ`, `getenv`, `.env.example`, `docker-compose.yml` → `environment` |
| a dependency or a version | the manifest (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`), the lockfile for what is actually resolved |
| a required runtime version | `.nvmrc`, `engines` in `package.json`, `python_requires`, `rust-version`, the Dockerfile base image |
| a port, host, or URL | server startup code, `docker-compose.yml` → `ports`, k8s manifests, the config defaults |
| a CLI flag or subcommand | the argument parser (`commander`, `yargs`, `argparse`, `clap`, `cobra`) |
| an API route | the router definitions |
| a config key or default value | the config schema / loader / defaults object |
| a described behaviour | the function or module the doc names |
| an architecture claim | the import graph — who actually calls whom |
| a test instruction | the test runner config plus how CI invokes it (CI is the ground truth when they disagree) |

## Useful checks

Real scripts, so you know which commands exist:

```bash
jq -r '.scripts | keys[]' package.json 2>/dev/null
grep -E '^[a-zA-Z0-9_-]+:' Makefile 2>/dev/null
```

Every command the doc claims, extracted for checking:

```bash
grep -oE '\b(npm|yarn|pnpm|make|python|poetry|uv|cargo|go|docker)\b[^`\n]*' README.md
```

Every path the doc mentions, and whether it exists:

```bash
grep -oE '`[^`]*/[^`]*`' README.md | tr -d '`' | sort -u | while read -r p; do
  [ -e "$p" ] || echo "MISSING: $p"
done
```

Env vars the code actually reads, to compare against the documented list:

```bash
grep -rhoE '(process\.env\.|os\.environ\[.|getenv\(.)[A-Z_][A-Z0-9_]*' src/ 2>/dev/null | sort -u
```

Adjust the paths and the language to the project. These are starting points, not a fixed procedure — a Go or Rust project needs different greps.

## Watch out for

**CI is more authoritative than the README, and often than the Makefile.** If CI runs `pytest -x --cov` and the README says `pytest`, CI is what actually has to pass.

**A command can exist and still be wrong.** `npm start` may exist but be the production entry point while newcomers need `npm run dev`. Check what the script *does*, not just that the key is present.

**Monorepos**: a command valid in `packages/api/` fails at the root. Note the working directory a command needs.

**Git history is a cheap tiebreaker for staleness.** `git log --oneline -3 -- <path>` on the doc versus the code it describes tells you which one moved last, and `git log --diff-filter=D --name-only` finds when a path the doc mentions was deleted.
