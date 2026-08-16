---
name: simplify-documentation
description: Simplify, shrink and fact-check existing project documentation against the code — agent files (CLAUDE.md, AGENTS.md, .cursorrules) get cut down to only what an agent cannot derive from the code itself, and human files (README.md, docs/**) get rewritten to be shorter, plainer and diagrammed with Mermaid. Use this skill whenever the user wants documentation cleaned up, trimmed, simplified, made readable, or checked for staleness — including phrasings like "simplifie / nettoie / allège / dégraisse la doc", "mon CLAUDE.md est trop long", "le README est obsolète / illisible", "la doc est encore juste après le refacto ?", "ajoute un schéma au README", "clean up the docs", "the README is out of date", "trim CLAUDE.md", "make this readable for humans" — even when the user does not say the word "documentation". Do not use it to write brand-new docs from scratch, to generate an initial CLAUDE.md (that is /init), or to maintain a CHANGELOG.
---

# Simplify Documentation

Documentation written alongside code drifts. Agent files accumulate rules that restate what the code already says, plus paths that no longer exist. READMEs keep describing a past version of the project. Both failure modes are expensive in different ways: a stale line in an agent file is *worse than nothing*, because the agent will act on it; a wrong README costs every newcomer an hour.

This skill fixes existing documentation. It does not write new documentation.

The one rule everything else follows from: **the code is the source of truth, so read the code before judging the doc.** Every claim you keep should be one you verified, and every claim you cut should be one you can justify.

## Two profiles, two goals

| | Agent files | Human files |
|---|---|---|
| Examples | `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `.github/copilot-instructions.md` | `README.md`, `docs/**`, `CONTRIBUTING.md` |
| Goal | Minimize. Every line costs tokens on every single invocation. | Clarify. Every line costs a human's attention once, but they give up fast. |
| Main lever | Delete what the code already tells the agent | Rewrite plainly, add a diagram, condense |
| Read next | `references/agent-docs.md` | `references/human-docs.md` |

Classify by filename first. If a file is ambiguous (a `docs/architecture.md` that reads like agent instructions), classify by content: imperative rules addressed to a tool → agent; explanation addressed to a person → human. When you genuinely cannot tell, ask.

## Workflow

### 1. Scope

**First, read the request's verb — it decides the deliverable.**

*Check* requests ("vérifie si la doc est encore juste", "is the README still accurate?", "did the refactor break the docs?") are questions. The answer is the report. Do not rewrite the files; end with the findings and an offer to fix them. Rewriting turns a question into a diff the user has to audit, which is more work than they asked for and destroys the thing they wanted to look at.

*Fix* requests ("simplifie", "nettoie", "dégraisse", "reprends le README", "clean this up") ask for a changed file. Report, then apply.

When the wording is genuinely ambiguous, treat it as a check. A report is cheap to turn into a rewrite; a rewrite is expensive to turn back into a question.

The user's stated scope binds too. If they asked about `CLAUDE.md` and the `README.md` turns out to be worse, say so in the report and leave the file alone — do not widen the job unasked.

Then find the candidates:

```bash
fd -e md -H --exclude node_modules --exclude vendor --exclude .git . | head -50
```

(or `find . -name '*.md' -not -path '*/node_modules/*' -not -path '*/.git/*'` if `fd` is unavailable)

Include `README.md`, `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `docs/**`, and per-package READMEs in a monorepo. Leave out `CHANGELOG*`, `LICENSE*`, anything under `node_modules`/`vendor`/`.git`, and tool-generated docs — an "auto-generated, do not edit" header, or the presence of a `typedoc.json`/`mkdocs.yml`/`sphinx` config, means the generator is the real source and editing the output gets overwritten.

Show the user what you found with line counts, and ask which files to work on:

```
README.md              71 lignes   (humain)
CLAUDE.md             201 lignes   (agent)
docs/deployment.md     54 lignes   (humain)
```

Asking matters here — the user often only cares about one of them, and processing all of them costs a lot of reading for nothing.

### 2. Establish ground truth

Before analysing the doc in detail, read the code. You are building a small fact sheet to check claims against:

- entry point(s) and how the thing actually starts
- real scripts: `package.json` scripts, `Makefile` targets, `pyproject.toml`, `justfile`, CI workflow steps
- real directory layout (top two levels is usually enough)
- environment variables the code actually reads
- dependencies and versions from the manifest
- how tests are actually run

Do this *first*. If you read the doc first, its claims anchor you and you start looking for confirmation instead of checking. `references/verification.md` lists where to check each kind of claim and how to classify the result.

### 3. Analyse

Read the reference file for the profile (`references/agent-docs.md` or `references/human-docs.md`), then go through the doc claim by claim and sort each one:

- **wrong** — the code contradicts it
- **redundant** — true, but the agent or reader gets it free from the code
- **rewritable** — true and useful, but bloated or unclear
- **unverifiable** — no trace in the code either way
- **keep** — true, useful, well put

### 4. Report before writing

Present findings and wait for the user's go-ahead. Rewriting someone's docs unannounced makes the diff the only place to discover what you did, which is a bad place to discover it.

```
## CLAUDE.md (201 lignes → ~60)

### Faux (le code dit le contraire)
- L.42 « lancer avec `npm start` » → ce script n'existe pas, c'est `npm run dev`
- L.88 référence à `src/legacy/` → dossier supprimé

### Redondant (déductible du code)
- L.60-95 arborescence des fichiers recopiée
- L.150-160 liste des dépendances

### À reformuler / condenser
- section « Architecture » : 40 lignes de prose → schéma Mermaid + 5 lignes

### Incertain — à trancher avec toi
- L.120 « ne jamais toucher au cache Redis » : aucune trace de Redis dans le
  code, mais ça peut être une contrainte d'infra que le code ne montre pas
```

When you cannot ask — a subagent, a hook, a scheduled run with no one to answer — do not stall waiting for approval that will never come, and do not skip the report. Write it to `doc-report.md` at the repo root. What happens next still depends on the verb from phase 1:

- a *check* request stops there: the report is the deliverable, and no file is rewritten
- a *fix* request proceeds on the safe subset — apply what the code contradicts, leave the uncertain items untouched and listed

Not being able to ask is a reason to be more conservative, not less.

The **uncertain** bucket is the one that protects the user. An unverifiable claim is not automatically false — it can be a team agreement, an infra constraint, a business rule, a hard-won lesson from an outage. Surface those and let the user decide; never delete them silently.

### 5. Apply, then check your own output

After the go-ahead, rewrite the files. Then re-read what you produced and verify:

- every command you kept or wrote exists and runs as written
- every path you mention exists
- every Mermaid block parses (see `references/human-docs.md` for the syntax traps)
- you did not introduce a claim that was not in the original and not verified

Close with a factual summary: lines before/after per file, what categories you removed, and what is still open (the uncertain items the user has not ruled on).

## Guardrails

**Do not invent content to fill a section.** If "Configuration" has nothing true to say, the section goes away. A plausible-sounding invented default is the worst possible outcome of a documentation cleanup — it is indistinguishable from a verified one to the next reader.

**Delete because it is wrong, duplicated, or derivable — not because it is long.** A 30-line section explaining a genuinely tricky invariant is doing its job. Length is a symptom you investigate, not a verdict.

**Leave alone**: license text, attribution and credits, security contacts, contribution instructions, badges, and code of conduct. These are there for legal or social reasons, not informational ones, and shortening them serves nobody.

**Keep the source language.** A French README stays French, an English CLAUDE.md stays English. Match the register too — do not turn a deliberately casual project README into corporate prose.

**Preserve structure the user relies on.** Anchors get linked from outside the repo (issues, wikis, other READMEs). When you rename or drop a heading, mention it in the summary so the user can check for inbound links.

**When the doc and the code disagree, the doc is what you fix.** Do not "fix" the code to match its documentation unless the user asks — that is a separate change with separate risks.

**When the code itself is broken, report it and stop there.** A documented command that cannot work (a script that crashes, a linter with no config, a step that needs a directory nobody creates) is a code problem wearing a documentation costume. Do not paper over it by writing the command as if it worked, and do not invent a workaround you have not run. Say what is broken, where, and leave it in the report — the user decides whether that becomes a second task.
