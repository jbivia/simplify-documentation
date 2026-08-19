#!/usr/bin/env python3
"""Mechanically checkable assertions for the simplify-documentation evals.

Usage:
    python3 evals/grade.py <run-dir> --eval 1

<run-dir> is a directory containing `outputs/` (the docs the run produced) and
`project/` (the working copy it edited). Prints a grading.json-shaped result to
stdout.

Only the assertions a script can settle are here. Judgement calls — "the gotcha
was preserved", "the diagram shows the mechanism" — are graded by a human or a
grader agent from the transcript.
"""

import argparse
import json
import re
import sys
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "sample-project"
FIXTURE_MULTI = Path(__file__).parent / "fixtures" / "multi-agent-docs"

ALWAYS_ON = ["CLAUDE.md", "AGENTS.md", ".cursorrules", ".github/copilot-instructions.md"]
MUST_NOT_TOUCH = ["src/feedscan/legacy/CLAUDE.md", ".cursor/rules/tests.mdc"]

REAL_SCRIPTS = {"dev", "worker", "test", "lint", "format", "migrate"}
GHOST_PATHS = ["src/legacy", "src/models"]
GHOST_DEPS = ["express", "sequelize"]


def read(path):
    return path.read_text(encoding="utf-8") if path.exists() else None


def check(results, text, passed, evidence):
    results.append({"text": text, "passed": bool(passed), "evidence": evidence})


def strip_code_blocks(md):
    """Docs may legitimately quote a wrong command while explaining it is wrong."""
    return re.sub(r"```.*?```", "", md, flags=re.S)


NEGATED = r"(there is no|there's no|no such|does not exist|doesn't exist|not a script|n'existe pas|pas de script|instead of|au lieu de|replaced by|remplac)"


def npm_commands(md):
    """Every npm script the doc tells the reader to run.

    A doc that says "there is no `npm start`, use `npm run dev`" is doing the
    right thing, so mentions inside a negation are not counted as citations.
    """
    found = set()
    for m in re.finditer(r"npm\s+(?:run\s+)?([a-z][a-z0-9:_-]*)", md):
        word = m.group(1)
        if word in {"install", "ci", "i", "exec", "init", "publish"}:
            continue
        line_start = md.rfind("\n", 0, m.start()) + 1
        line_end = md.find("\n", m.end())
        line = md[line_start : line_end if line_end != -1 else len(md)]
        line = re.sub(r"[*_`]", "", line)  # "there is **no** `npm start`"
        if re.search(NEGATED, line, re.I) or re.search(NEGATIONS, line, re.I):
            continue
        found.add(word)
    return found


def cited_paths(md):
    """Backticked tokens that look like a repo-relative path.

    Deliberately excludes API routes (`/jobs/:id`), URLs and flags — they are
    not filesystem paths and flagging them would be noise.
    """
    out = set()
    for m in re.finditer(r"`([^`\n]+)`", md):
        tok = m.group(1).strip()
        if " " in tok or ":" in tok or tok.startswith(("http", "-", "/")):
            continue
        if re.match(r"^\.?/?[a-zA-Z0-9_.-]+/", tok):
            clean = tok.lstrip("./").rstrip("/")
            # A bare top-level name (`data/`) is usually a runtime directory the
            # docs tell you to create, not a source path claim.
            if "/" in clean:
                out.add(clean)
    return out


NEGATIONS = (
    r"(no longer|does not exist|doesn't exist|there (is|are) no|no such|removed|dropped|"
    r"deleted|gone|do not (introduce|add|use)|don't (introduce|add|use)|never (add|use)|"
    r"n'existe plus|n'existe pas|supprim|inexistant|obsol|ne pas (ajouter|utiliser))"
)


def presented_as_existing(md, needle):
    """True if `needle` appears without a nearby statement that it is gone.

    A cleaned-up doc is allowed — sometimes required — to say "src/legacy/ no
    longer exists", or "do not introduce Express". What must not survive is the
    doc still treating the thing as part of the project.
    """
    text = re.sub(r"[*_`]", "", md)
    for m in re.finditer(re.escape(needle), text, re.I):
        start = text.rfind("\n\n", 0, m.start()) + 1
        end = text.find("\n\n", m.end())
        context = text[start : end if end != -1 else len(text)]
        if not (re.search(NEGATIONS, context, re.I) or re.search(NEGATED, context, re.I)):
            return True
    return False


def mermaid_blocks(md):
    return re.findall(r"```mermaid\n(.*?)```", md, flags=re.S)


def mermaid_problems(block):
    """Syntax traps that break rendering on GitHub."""
    problems = []
    # Quoted labels are always safe, and their contents would otherwise confuse
    # the bracket scan below — blank them out first.
    scan = re.sub(r'"[^"\n]*"', '""', block)
    # Node shapes: [text] [(cyl)] ((circle)) [[subroutine]] {rhombus} {{hexagon}}
    for m in re.finditer(r"[A-Za-z0-9_]+[\[\({]{1,2}([^\]\)}\n]*)[\]\)}]{1,2}", scan):
        label = m.group(1).strip()
        if label and label != '""' and re.search(r"[():/]", label):
            problems.append(f"unquoted label with special chars: {label}")
    if re.search(r"-->\s*\[", block):
        problems.append("edge label uses --> [text] instead of -->|text|")
    if re.search(r"^\s*stateDiagram\s*$", block, flags=re.M):
        problems.append("stateDiagram instead of stateDiagram-v2")
    first = next((l.strip() for l in block.splitlines() if l.strip()), "")
    if not re.match(r"(flowchart|graph|sequenceDiagram|stateDiagram-v2|classDiagram|erDiagram)", first):
        problems.append(f"unrecognised diagram type: {first!r}")
    return problems


def near(text, needle, window=400):
    """Text within `window` chars around each occurrence of `needle`."""
    out = []
    for m in re.finditer(re.escape(needle), text, re.I):
        out.append(text[max(0, m.start() - window) : m.end() + window])
    return "\n".join(out)


def unchanged(project, rel, fixture=None):
    src = (fixture or FIXTURE_MULTI) / rel
    dst = project / rel
    if not dst.exists():
        return False, "file is gone"
    if not src.exists():
        return False, "missing from the fixture"
    same = src.read_text(encoding="utf-8") == dst.read_text(encoding="utf-8")
    return same, "identical" if same else "modified"


def grade_consolidation(run_dir):
    """Eval 4: several agent instruction files coexist."""
    out, project = run_dir / "outputs", run_dir / "project"
    results = []
    # Compare against the fixture as it was when the run happened, if the
    # workspace kept a snapshot. Without it, any later fixture edit would make
    # untouched files look modified on a re-grade.
    snapshot = run_dir.parent / "fixture-snapshot"
    baseline = snapshot if snapshot.is_dir() else FIXTURE_MULTI

    reports = [p for p in list(out.glob("*.md")) + list(project.glob("*.md"))
               if p.name not in set(ALWAYS_ON) | {"agent-summary.md"}]
    stated = {p.name: p for p in reports}
    summary = run_dir / "agent-summary.md"
    text = "\n".join((read(p) or "") for p in list(stated.values()) + ([summary] if summary.exists() else []))
    merged = "\n".join((read(out / n) or "") for n in ALWAYS_ON)
    proposed = text + "\n" + merged  # merged content may live in the report or in a file

    check(results, "A written findings report exists", bool(stated),
          f"report files: {sorted(stated)}" if stated else "no report file found")

    seen = [n for n in ALWAYS_ON if re.search(re.escape(Path(n).name), text, re.I)]
    check(results, "All four always-on agent files were examined", len(seen) == len(ALWAYS_ON),
          f"mentioned: {seen}")

    # --- contradictions surfaced, and settled the right way ---
    pairs = [
        ("poetry vs uv", r"poetry", r"\buv\b|uv sync"),
        ("test naming", r"test_\*|test_parse|test_\{", r"\*_test|_test\.py"),
        ("Python version", r"3\.10", r"3\.12"),
    ]
    for label, a, b in pairs:
        hit = bool(re.search(a, text, re.I) and re.search(b, text, re.I))
        check(results, f"The report surfaces the {label} contradiction", hit,
              "both sides mentioned" if hit else "not both sides")

    lock = bool(re.search(r"uv\.lock", text, re.I))
    check(results, "poetry vs uv is settled by pointing at the code (uv.lock)", lock,
          "uv.lock cited" if lock else "uv.lock never cited")

    real = bool(re.search(r"test_(parse|store|cli)\.py|tests/ contient|files in tests/", text, re.I))
    check(results, "The test naming contradiction is settled by the real filenames", real,
          "real test filenames cited" if real else "no reference to the actual files")

    db = bool(re.search(r"disposable|jetable|never delete|ne jamais supprimer", text, re.I))
    check(results, "The report surfaces the database-deletion contradiction", db,
          "mentioned" if db else "absent")

    ctx = near(text, "feedscan.db") + near(text, "disposable") + near(text, "Never delete")
    arb = bool(re.search(r"trancher|\bto you\b|your call|cannot be settled|ne peut pas .{0,20}trancher|"
                         r"incertain|uncertain|arbitrage|\bdecide\b|à toi", ctx, re.I))
    check(results, "The database contradiction is left for the user, not resolved unilaterally", db and arb,
          "raised for arbitration" if (db and arb) else "no sign it was left open")

    # --- the two options ---
    opt_a = bool(re.search(r"AGENTS\.md", text, re.I) and re.search(r"@AGENTS\.md|bridge|pont|pointeur", text, re.I))
    opt_b = bool(re.search(r"(un seul|single|only one|unique) .{0,20}CLAUDE\.md|CLAUDE\.md (seul|only|unique)", text, re.I))
    check(results, "Both consolidation options are presented", opt_a and opt_b,
          f"option A: {opt_a}, option B: {opt_b}")

    cost = bool(re.search(r"perd|perte|lose|loses|au prix de|cost|compatibilit", text, re.I))
    check(results, "The cost of each option is stated", cost,
          "costs discussed" if cost else "no trade-off stated")

    symlink = bool(re.search(r"ln -s|symlink|lien symbolique", proposed, re.I))
    imports = bool(re.search(r"@AGENTS\.md", proposed))
    check(results, "A proposed bridge uses the @AGENTS.md import, not a symlink",
          imports and not symlink,
          f"@import: {imports}, symlink mentioned: {symlink}")

    # --- what must not be touched ---
    for rel in MUST_NOT_TOUCH:
        ok, why = unchanged(project, rel, baseline)
        check(results, f"{rel} is untouched", ok, why)

    missing = [n for n in ALWAYS_ON if not (project / n).exists()]
    check(results, "No agent instruction file was deleted", not missing,
          f"deleted: {missing}" if missing else "all four still present")

    # --- content that must survive into whatever is proposed ---
    survives = [
        ("the lenient date-parsing gotcha", r"pubDate|lenient|None rather than|malformed date|dates? .{0,30}(cass|broken)"),
        ("the missing-link gotcha", r"no <?link|sans lien|drops items|primary key in `?entries|clé primaire"),
        ("the feeds.txt format from AGENTS.md", r"feeds\.txt"),
    ]
    for label, pattern in survives:
        hit = bool(re.search(pattern, proposed, re.I))
        check(results, f"{label} is preserved", hit, "present" if hit else "lost")

    # --- code left alone ---
    changed = []
    for src in list((baseline / "src").rglob("*.py")) + list((baseline / "tests").rglob("*.py")):
        rel = src.relative_to(baseline)
        ok, _ = unchanged(project, str(rel), baseline)
        if not ok:
            changed.append(str(rel))
    check(results, "No source file under src/ or tests/ was modified", not changed,
          f"modified: {changed}" if changed else "all source files identical")

    passed = sum(r["passed"] for r in results)
    return {"expectations": results,
            "summary": {"passed": passed, "failed": len(results) - passed, "total": len(results),
                        "pass_rate": round(passed / len(results), 3) if results else 0.0}}


def grade(run_dir, eval_id):
    if eval_id == 4:
        return grade_consolidation(run_dir)

    out = run_dir / "outputs"
    project = run_dir / "project"
    results = []

    claude = read(out / "CLAUDE.md")
    readme = read(out / "README.md")
    # A run that reports its findings only in its reply still found them. Those
    # findings are graded from `agent-summary.md` (the run's returned text), but
    # only a real file counts as "a written report" — a reply scrolls away.
    seen_names = set()
    reports = []
    for p in list(out.glob("*.md")) + list(project.glob("*.md")):
        if p.name in {"CLAUDE.md", "README.md", "agent-summary.md"} or p.name in seen_names:
            continue
        seen_names.add(p.name)
        reports.append(p)
    stated = reports + [p for p in (run_dir / "agent-summary.md",) if p.exists()]

    orig_claude = read(FIXTURE / "CLAUDE.md") or ""
    orig_readme = read(FIXTURE / "README.md") or ""

    check(results, "A written findings report exists", bool(reports),
          f"report files: {[p.name for p in reports]}" if reports else "no report file found")

    # --- eval 3 is a *check* request: the report is the deliverable ---
    if eval_id == 3:
        report_text = "\n".join(read(p) or "" for p in stated)
        for label, produced, original in (("CLAUDE.md", claude, orig_claude),
                                          ("README.md", readme, orig_readme)):
            unchanged = produced is None or produced == original
            check(results, f"{label} was left unmodified (the user asked for a check, not a fix)",
                  unchanged, "unchanged" if unchanged else
                  f"rewritten ({len(original.splitlines())} -> {len(produced.splitlines())} lines)")
        findings = {
            "src/legacy does not exist": r"legacy",
            "src/models does not exist": r"models",
            "npm start does not exist": r"npm\s+start",
            "the port mismatch (8080 vs 3000)": r"8080",
            "express is not a dependency": r"express",
            "sequelize is not a dependency": r"sequelize",
            "REDIS_URL is never read": r"REDIS_URL",
            "the Node version mismatch": r"(node\s*(\.js)?\s*(16|>=?\s*20)|engines)",
            "the worker is a separate process": r"worker",
        }
        for label, pattern in findings.items():
            hit = bool(re.search(pattern, report_text, re.I))
            check(results, f"The report identifies that {label}", hit,
                  "found in report" if hit else "not found in report")
        uncertain = re.search(r"(uncertain|incertain|unverifiable|invérifiable|à trancher|"
                              r"needs? (a )?(human|your|ops)|cannot verify|no trace)", report_text, re.I)
        check(results, "The report separates unverifiable claims from confirmed contradictions",
              bool(uncertain), uncertain.group(0) if uncertain else "no uncertainty section found")
        located = len(re.findall(r"(L\.?\s?\d+|line\s+\d+|:\d+|##+\s)", report_text))
        check(results, "The findings cite locations rather than being vague", located >= 5,
              f"{located} location markers")
        passed = sum(r["passed"] for r in results)
        return {"expectations": results,
                "summary": {"passed": passed, "failed": len(results) - passed,
                            "total": len(results),
                            "pass_rate": round(passed / len(results), 3) if results else 0.0}}

    # --- assertions on CLAUDE.md ---
    if eval_id == 1 and claude is not None:
        before, after = len(orig_claude.splitlines()), len(claude.splitlines())
        check(results, "CLAUDE.md is at most 50% of its original line count",
              after <= before * 0.5, f"{before} -> {after} lines")
        for ghost in GHOST_PATHS:
            live = presented_as_existing(claude, ghost)
            check(results, f"CLAUDE.md no longer presents {ghost}/ as existing", not live,
                  "still presented as real" if live else "absent, or explicitly marked as gone")
        for dep in GHOST_DEPS:
            live = presented_as_existing(claude, dep)
            check(results, f"CLAUDE.md no longer lists {dep} as a dependency", not live,
                  "still listed" if live else "absent, or explicitly marked as gone")
        bad = npm_commands(claude) - REAL_SCRIPTS
        check(results, "Every npm script cited in CLAUDE.md exists in package.json",
              not bad, f"unknown scripts: {sorted(bad)}" if bad else "all cited scripts exist")
        check(results, "The recopied directory tree was removed from CLAUDE.md",
              "├──" not in claude and "└──" not in claude,
              "tree drawing absent" if "├──" not in claude else "tree drawing still present")
        check(results, "Generic engineering advice was removed from CLAUDE.md",
              not re.search(r"clean, readable|handle errors properly|best practices", claude, re.I),
              "generic advice absent" if not re.search(r"clean, readable|handle errors properly", claude, re.I)
              else "generic advice still present")
        check(results, "The Redis instruction is not silently dropped (kept or reported)",
              ("redis" in claude.lower()) or any("redis" in (read(p) or "").lower() for p in stated),
              "mentioned in output or report" if ("redis" in claude.lower() or
              any("redis" in (read(p) or "").lower() for p in stated)) else "vanished without mention")

    # --- assertions on README.md ---
    if eval_id == 2 and readme is not None:
        before, after = len(orig_readme.splitlines()), len(readme.splitlines())
        if True:
            # Counting whole lines would punish adding a diagram, which is the
            # point of this eval. What has to shrink is the prose.
            prose_before = len(strip_code_blocks(orig_readme).splitlines())
            prose_after = len(strip_code_blocks(readme).splitlines())
            check(results, "The prose shrank (line count outside code blocks)",
                  prose_after < prose_before,
                  f"prose {prose_before} -> {prose_after} lines (whole file {before} -> {after})")
            blocks = mermaid_blocks(readme)
            check(results, "README contains a mermaid block", bool(blocks), f"{len(blocks)} block(s)")
            problems = [p for b in blocks for p in mermaid_problems(b)]
            check(results, "Mermaid blocks have no known syntax problems",
                  bool(blocks) and not problems,
                  "; ".join(problems) if problems else
                  ("no problems detected" if blocks else "no diagram to check"))
            labelled = any(re.search(r"-->\|", b) or "->>" in b for b in blocks)
            check(results, "Mermaid edges are labelled with what flows", labelled,
                  "labelled edges found" if labelled else "no labelled edges")
            check(results, "README documents starting the worker separately",
                  "npm run worker" in readme,
                  "npm run worker present" if "npm run worker" in readme else "worker command absent")
            check(results, "README mentions the migration step",
                  "migrate" in readme, "migrate mentioned" if "migrate" in readme else "migrate absent")
        body = strip_code_blocks(readme)
        check(results, "README no longer advertises port 8080",
              "8080" not in readme, "absent" if "8080" not in readme else "8080 still present")
        check(results, "README no longer lists REDIS_URL",
              "REDIS_URL" not in body, "absent" if "REDIS_URL" not in body else "still listed")
        check(results, "README lists QUEUE_POLL_MS",
              "QUEUE_POLL_MS" in readme, "present" if "QUEUE_POLL_MS" in readme else "missing")
        check(results, "README states a Node requirement consistent with engines (>=20)",
              not re.search(r"[Nn]ode(\.js)?\s*(version\s*)?1[0-9]", body),
              "no stale Node version" if not re.search(r"[Nn]ode(\.js)?\s*(version\s*)?1[0-9]", body)
              else "still claims Node 1x")
        check(results, "README no longer claims the worker starts automatically",
              not re.search(r"worker is started automatically|automatically as part of the server", readme, re.I),
              "claim removed" if not re.search(r"started automatically", readme, re.I) else "claim still present")
        bad = npm_commands(readme) - REAL_SCRIPTS
        check(results, "Every npm script cited in README exists in package.json",
              not bad, f"unknown scripts: {sorted(bad)}" if bad else "all cited scripts exist")
        check(results, "README does not tell the reader to run `npm install --production`",
              "--production" not in readme,
              "absent" if "--production" not in readme else "still present")
        check(results, "The license section was preserved", "MIT" in readme,
              "MIT present" if "MIT" in readme else "license lost")

    # --- no invented paths, in the files this run actually rewrote ---
    for label, text, original in (("CLAUDE.md", claude, orig_claude), ("README.md", readme, orig_readme)):
        if not text or text == original:
            continue  # untouched file: its errors belong to another eval
        # A path whose parent directory does not exist is most likely a runtime
        # artefact (./data/app.db) rather than a stale source path.
        missing = sorted(p for p in cited_paths(text)
                         if not (FIXTURE / p).exists() and (FIXTURE / p).parent.exists()
                         and presented_as_existing(text, p))
        check(results, f"Every source path cited in {label} exists in the project",
              not missing, f"missing: {missing}" if missing else "all cited paths exist")

    passed = sum(r["passed"] for r in results)
    return {
        "expectations": results,
        "summary": {
            "passed": passed,
            "failed": len(results) - passed,
            "total": len(results),
            "pass_rate": round(passed / len(results), 3) if results else 0.0,
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--eval", type=int, required=True, choices=[1, 2, 3, 4])
    ap.add_argument("--write", action="store_true", help="write grading.json into run_dir")
    args = ap.parse_args()

    if not args.run_dir.exists():
        sys.exit(f"no such run dir: {args.run_dir}")

    result = grade(args.run_dir, args.eval)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.write:
        (args.run_dir / "grading.json").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
