# Agent-facing docs (CLAUDE.md, AGENTS.md, .cursorrules)

## The economics

An agent file is loaded into context on every single invocation, forever. A line that says something the agent would have discovered anyway by reading the code is not neutral — it costs tokens each time and it dilutes the lines that actually matter. The test for every line is:

> Would an agent that reads this codebase already know this?

If yes, it goes. What survives is the knowledge that is *not* in the code: conventions, gotchas, prohibitions, and the reasons behind them.

## Order of operations

Work in this order — it saves effort, because each pass shrinks the input to the next:

1. **Remove what is false.** Highest value, lowest risk. A stale instruction actively causes wrong behaviour.
2. **Remove what is derivable.** True but free.
3. **Condense what is left.** Same facts, fewer words.

Do not start by rewriting prose. You will spend effort polishing lines you are about to delete.

## Cut these

**Recopied directory trees.** The agent can run `ls`. A tree also rots the fastest of anything in the file.

**Dependency lists and versions.** The manifest is authoritative and always current; the copy never is.

**Generic engineering advice.** "Write clean code", "add tests for new features", "handle errors properly", "follow best practices". This is already in the model. It displaces project-specific knowledge and teaches the agent nothing.

**Explanations of standard tooling.** What Jest is, what a git branch is, how npm works.

**Rules the linter, formatter, or CI already enforces.** If `prettier` sets the quote style, saying it in prose adds a second source of truth that can drift. Point at the config instead: `formatting: see .prettierrc`.

**History, changelogs, migration notes.** "We used to use X, now we use Y." The agent only needs the current state. If the migration is incomplete and both exist, that is a *gotcha* — rewrite it as one.

**Long code examples copied from the repo.** Reference the file path instead. The copy drifts; the path does not.

**Preambles and sign-offs.** "This document describes...", "Thanks for reading!", "Feel free to update this file." Nothing acts on them.

**Duplicated rules.** Long agent files often say the same thing in three sections. Keep the clearest statement, in the most relevant section.

## Keep these

**Commands that are not guessable.** Tests that need a specific flag, a service that must be running first, a build with a required env var, a non-standard test runner invocation.

**Project-specific conventions.** Where new modules go, how files are named, which layer may import which, the error-handling pattern the codebase actually uses.

**Gotchas.** The knowledge that costs an hour to rediscover: "the API returns 200 on failure — check the `status` field", "the dev server does not hot-reload the config; restart it", "`yarn test` passes locally but CI uses a different TZ".

**Prohibitions with their reason.** "Don't edit `generated/` — it's rebuilt by `make proto`." The reason is what makes the rule survive contact with a situation you did not anticipate; a bare "never do X" gets worked around.

**Paths to genuinely central files.** Not the whole tree — the three or four files where things actually happen.

**Anything about the environment the code cannot show.** Staging credentials live in 1Password, the CI runner has no network, the prod database is read-only from this repo.

## Format

- Imperative and dense. "Run X before Y", not "It is recommended that you run X before Y."
- Short bullets grouped under short headings. Headings let the agent skim to the relevant part.
- No intro, no conclusion, no transitions.
- Concrete over abstract: a command the agent can paste beats a description of what the command does.

## Before / after

**Before (17 lines):**

```markdown
## Project Structure

This project follows a standard Node.js structure. The source code is
located in the `src/` directory, which contains the following subfolders:

- `src/api/` - API routes and handlers
- `src/models/` - Database models
- `src/utils/` - Utility functions
- `src/legacy/` - Old code, being migrated

Tests are in the `tests/` folder. Configuration files are at the root.

## Testing

We use Jest for testing. Jest is a JavaScript testing framework that
lets you write unit tests. Please make sure to write tests for any new
features you add, and always run the test suite before committing.
```

**After (3 lines):**

```markdown
- Tests: `npm test -- --runInBand` (parallel runs share the test DB and flake)
- `src/legacy/` no longer exists — code moved to `src/api/`
```

What happened: the tree is derivable (`ls`), Jest is standard knowledge, "write tests" is generic advice. What survived is the one non-obvious thing (the `--runInBand` requirement and *why*). The `src/legacy/` line only stays if the path is still referenced elsewhere and the correction is worth stating; otherwise it goes too.

**Before (5 lines):**

```markdown
## Code Style

Use 2 spaces for indentation. Always use single quotes for strings.
Add semicolons at the end of statements. Maximum line length is 100
characters. Use camelCase for variables and PascalCase for classes.
```

**After (1 line, assuming a Prettier config exists):**

```markdown
- Style is enforced by Prettier (`.prettierrc`) — run `npm run format`, don't hand-tune
```

If no formatter config exists, the rules are load-bearing and stay — but then they are worth condensing to one line, not five.

## How far to go

A focused agent file for a mid-sized project usually lands between 20 and 80 lines. If you are still above 150 after all three passes, look for a whole category you have not questioned yet — usually a long "architecture" narrative that is really just the file tree in prose.

Do not chase a number. If a project genuinely has fifteen gotchas, keep fifteen gotchas.
