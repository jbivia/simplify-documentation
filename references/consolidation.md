# Consolidating agent instruction files that coexist

A project picks these up one at a time: `CLAUDE.md` when someone starts using Claude Code, `.cursorrules` from a stint in Cursor, `.github/copilot-instructions.md` added by a colleague, `AGENTS.md` for the cross-tool convention. Each then drifts on its own.

The expensive failure is not the duplication — it is that **two agents reading two different files behave differently on the same repository**, and nobody notices because nobody reads all of them side by side. Surfacing those contradictions is the most valuable thing this pass produces, well ahead of the file count going down.

## Detection

### Always-on files — candidates for unification

```
CLAUDE.md                          AGENTS.md
.cursorrules                       .clinerules
.windsurfrules                     .agent.md
.github/copilot-instructions.md    .claude/rules/*.md
.devin/rules/*.md
```

### Conditionally loaded — leave in place

These only load for files matching their `globs` / `applyTo` frontmatter:

```
.cursor/rules/*.mdc                     globs:, alwaysApply
.github/instructions/*.instructions.md  applyTo:
.windsurf/rules/*.md                    globs:
```

Flattening them into a single always-on file changes their semantics: a rule scoped to `tests/**` becomes a rule that loads on every invocation. That costs context every time and risks applying advice where it does not belong. An `.mdc` with `alwaysApply: true` and no `globs` is effectively always-on and *can* be merged — check the frontmatter rather than the directory.

### Never sweep in

**Nested `CLAUDE.md` / `AGENTS.md` in subdirectories.** Directory-scoped instructions are a feature: they load when work touches that directory. Merging them into the root makes them permanent and severs them from what they describe.

**`CLAUDE.local.md`** — personal, usually gitignored. Not the project's to consolidate.

**Configuration** — `.mcp.json`, `.claude/settings.json`, hooks, `.aider.conf.yml`. Not prose, not instructions.

**`~/.claude/CLAUDE.md`** — user-level, outside the repository entirely.

### Finding them

```bash
ls -a | grep -iE '^(CLAUDE|AGENTS|AGENT)\.md$|^\.(cursorrules|clinerules|windsurfrules)$'
ls .github/copilot-instructions.md .claude/rules/*.md 2>/dev/null
# scoped rules — read the frontmatter before deciding
head -5 .cursor/rules/*.mdc .github/instructions/*.instructions.md 2>/dev/null
# nested files, which stay where they are
find . -mindepth 2 -name 'CLAUDE.md' -o -mindepth 2 -name 'AGENTS.md' | grep -v node_modules
```

## When not to propose consolidation

Measure before proposing. Consolidation is work, and it is not always an improvement.

- **One always-on file.** Nothing to consolidate.
- **One of them is already a pointer.** A three-line `AGENTS.md` saying "see CLAUDE.md" *is* the consolidated state. Say so and move on.
- **The contents genuinely do not overlap.** A `copilot-instructions.md` that only covers PR description style says nothing to Claude Code. Merging it adds noise to every invocation for no gain.

Quantify the overlap in the report — "roughly 80% of `.cursorrules` restates `CLAUDE.md`" is actionable; "there are several files" is not.

## The two options

| | A — `AGENTS.md` canonical | B — `CLAUDE.md` only |
| --- | --- | --- |
| what exists after | `AGENTS.md` + a two-line `CLAUDE.md` bridge | one `CLAUDE.md` |
| other agents | keep working | lose their instructions entirely |
| new tool joins later | already fed | needs another file, and the drift starts again |
| cost | one extra file, and a bridge whose behaviour depends on import support | none |
| right when | more than one tool is in use, or might be | the team is Claude Code only and expects to stay there |

**A third outcome is legitimate: do not unify.** If the files are genuinely tool-specific, leaving them alone and fixing each in place is the better answer. Offer it.

## The compatibility bridge (option A)

`CLAUDE.md` becomes:

```markdown
@AGENTS.md

This project's instructions live in `AGENTS.md`. If you are reading this
without seeing their content, open `AGENTS.md` before doing anything else.
```

Two lines, and the second one is not decoration. `@path` imports are supported by Claude Code, but whether a given version *also* discovers `AGENTS.md` on its own is a version-dependent detail you should not assert. If imports resolve, the sentence is harmless noise. If they do not, that sentence is the only thing standing between the agent and an empty instruction file — it degrades to a readable instruction instead of a silent nothing.

**A symlink is the obvious alternative and is worse.** On a Windows clone with `core.symlinks=false`, git materialises `CLAUDE.md` as a ten-byte text file containing the string `AGENTS.md`, which the agent then reads as the complete instructions. It fails silently, on someone else's machine, which is the exact failure mode this skill exists to prevent.

Tell the user how to confirm: `/memory` lists the memory files actually loaded. That check takes seconds and settles the question for their version.

## Merge procedure

Order matters — each step shrinks the input to the next.

**1. Inventory.** Read every file in scope and list its claims. Do not start editing.

**2. Classify each claim.**

| | action |
| --- | --- |
| identical across files | keep once |
| overlapping, worded differently | keep the clearest statement |
| **contradictory** | stop — this needs the user, see below |
| tool-specific and still meaningful | keep, marked with which tool it serves |
| tool-specific and obsolete | drop, and say so in the report |

**3. Reduce.** Only now apply `references/agent-docs.md` to the union. Three overlapping files produce a bloated draft: the recopied tree appears three times, the generic advice twice, the dependency list in all of them. Reducing before deduplicating wastes effort on lines about to disappear.

**4. Verify against the code.** A merge is an excellent moment to discover that the three files are stale in three different ways — each froze at the moment its tool stopped being used. Run the usual checks from `references/verification.md` on the merged content.

**5. Remove the sources last**, after the unified file is written and checked. Git holds the history; do not leave `.bak` copies. Deleting files is the one irreversible-feeling step, so it needs explicit agreement even when the rest of the pass was already approved.

## Contradictions

Report them first, above everything else, with both versions quoted and located:

```
### Contradiction entre fichiers — à trancher

Installation
  CLAUDE.md L.12      « installer avec `poetry install` »
  AGENTS.md L.8       « installer avec `uv sync` »
  Le code : uv.lock présent, pas de poetry.lock -> AGENTS.md semble à jour

Nommage des tests
  CLAUDE.md L.40      « fichiers en test_*.py »
  .cursorrules L.15   « fichiers en *_test.py »
  Le code : les 14 fichiers de tests/ sont en test_*.py -> CLAUDE.md
```

When the code settles it, say so — that is a finding, not an arbitration. When it does not, **do not pick a winner**. Two contradictory rules that survived means two people believed different things; guessing which one to keep silently discards someone's reason.

## Mechanics

```bash
git mv CLAUDE.md AGENTS.md        # keeps the file's history
```

Then check, before writing the bridge:

- **Is `CLAUDE.md` gitignored?** Some setups ignore it. The bridge would then not be versioned, and only the person who ran the consolidation would have it.
- **Is there a nested `CLAUDE.md` deeper in the tree?** It stays, and it now sits under a root file with a different name — worth a line in the report so nobody hunts for the mismatch later.
- **Does anything reference the old paths?** A README, a CONTRIBUTING, a CI step that cats `.cursorrules`. Grep for the filenames you are about to delete.

Finish with the usual output check from the main workflow: every command in the merged file exists, every path resolves, nothing was invented while stitching two sources together.
