#!/usr/bin/env python3
"""Static checks on the skill itself. Run before committing.

    python3 evals/check_skill.py

Exists because a colon-space inside the unquoted YAML description silently
breaks the frontmatter, and a skill whose frontmatter does not parse never
loads at all — the most expensive failure this repository can ship.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_SKILL_LINES = 200
problems = []


def fail(msg):
    problems.append(msg)


skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

# --- frontmatter ---
m = re.match(r"^---\n(.*?)\n---\n", skill, re.S)
if not m:
    fail("SKILL.md has no YAML frontmatter")
else:
    try:
        import yaml

        meta = yaml.safe_load(m.group(1))
    except ImportError:
        meta = None
        print("note: pyyaml absent, frontmatter parsed by pattern only")
    except Exception as exc:
        meta = None
        fail(f"frontmatter does not parse as YAML: {exc}")
    if meta is not None:
        for key in ("name", "description"):
            if not meta.get(key):
                fail(f"frontmatter is missing `{key}`")
        if meta.get("name") != ROOT.name:
            fail(f"frontmatter name {meta.get('name')!r} != directory name {ROOT.name!r}")
    # The trap that caused this script to exist.
    for line in m.group(1).splitlines():
        key, _, value = line.partition(":")
        if value and not value.strip().startswith(("|", ">", '"', "'")) and ": " in value:
            fail(f"`{key}` holds an unquoted value containing ': ' — YAML reads it as a mapping")

# --- size ---
n = len(skill.splitlines())
if n > MAX_SKILL_LINES:
    fail(f"SKILL.md is {n} lines, over the {MAX_SKILL_LINES}-line budget")

# --- every referenced file exists ---
for doc in [ROOT / "SKILL.md", *(ROOT / "references").glob("*.md")]:
    for ref in set(re.findall(r"references/[a-z0-9-]+\.md", doc.read_text(encoding="utf-8"))):
        if not (ROOT / ref).exists():
            fail(f"{doc.name} points at {ref}, which does not exist")

# --- unreachable references ---
cited = set(re.findall(r"references/[a-z0-9-]+\.md", skill))
for ref in sorted((ROOT / "references").glob("*.md")):
    rel = f"references/{ref.name}"
    if rel not in cited:
        fail(f"{rel} exists but SKILL.md never sends the model to it")

# --- code fences balance, per file ---
for doc in [ROOT / "SKILL.md", *(ROOT / "references").glob("*.md")]:
    body = doc.read_text(encoding="utf-8")
    triple = len(re.findall(r"^```(?!`)", body, re.M))
    quad = len(re.findall(r"^````", body, re.M))
    if triple % 2 or quad % 2:
        fail(f"{doc.name} has unbalanced code fences ({triple} ``` and {quad} ````)")

# --- evals wiring ---
evals = json.loads((ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))
ids = [e["id"] for e in evals["evals"]]
if len(ids) != len(set(ids)):
    fail(f"duplicate eval ids: {ids}")
for e in evals["evals"]:
    for f in e.get("files", []):
        if not (ROOT / f).exists():
            fail(f"eval {e['id']} points at {f}, which does not exist")
    if not e.get("expectations"):
        fail(f"eval {e['id']} has no expectations")
grade = (ROOT / "evals" / "grade.py").read_text(encoding="utf-8")
declared = re.search(r"choices=\[([\d, ]+)\]", grade)
if declared:
    known = [int(x) for x in declared.group(1).replace(" ", "").split(",")]
    missing = sorted(set(ids) - set(known))
    if missing:
        fail(f"evals.json defines cases {missing} that grade.py cannot grade")

if problems:
    print(f"{len(problems)} problème(s) :")
    for p in problems:
        print(f"  - {p}")
    sys.exit(1)
print(f"OK — SKILL.md {n} lignes, {len(ids)} cas d'eval, toutes les références résolues")
