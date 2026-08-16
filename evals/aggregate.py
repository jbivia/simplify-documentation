#!/usr/bin/env python3
"""Aggregate per-run grading.json + timing.json into benchmark.json.

Usage:
    python3 evals/aggregate.py <iteration-dir>

Expects <iteration-dir>/eval-<id>-<name>/{with_skill,without_skill}/ each
holding grading.json and timing.json. Writes benchmark.json in the schema the
skill-creator eval viewer reads.
"""

import json
import statistics
import sys
from pathlib import Path

CONFIGS = ["with_skill", "without_skill"]


def load(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def stats(values):
    if not values:
        return {"mean": 0, "stddev": 0, "min": 0, "max": 0}
    return {
        "mean": round(statistics.mean(values), 3),
        "stddev": round(statistics.stdev(values), 3) if len(values) > 1 else 0.0,
        "min": round(min(values), 3),
        "max": round(max(values), 3),
    }


def main():
    iteration = Path(sys.argv[1])
    runs, by_config = [], {c: {"pass_rate": [], "time_seconds": [], "tokens": []} for c in CONFIGS}

    for eval_dir in sorted(iteration.glob("eval-*")):
        eval_id = int(eval_dir.name.split("-")[1])
        eval_name = eval_dir.name.split("-", 2)[2]
        for config in CONFIGS:
            grading = load(eval_dir / config / "grading.json")
            timing = load(eval_dir / config / "timing.json") or {}
            if not grading:
                continue
            s = grading["summary"]
            result = {
                "pass_rate": s["pass_rate"],
                "passed": s["passed"],
                "failed": s["failed"],
                "total": s["total"],
                "time_seconds": timing.get("total_duration_seconds", 0),
                "tokens": timing.get("total_tokens", 0),
                "tool_calls": timing.get("tool_uses", 0),
                "errors": 0,
            }
            runs.append({
                "eval_id": eval_id,
                "eval_name": eval_name,
                "configuration": config,
                "run_number": 1,
                "result": result,
                "expectations": grading["expectations"],
                "notes": [e["text"] for e in grading["expectations"] if not e["passed"]],
            })
            by_config[config]["pass_rate"].append(result["pass_rate"])
            by_config[config]["time_seconds"].append(result["time_seconds"])
            by_config[config]["tokens"].append(result["tokens"])

    summary = {c: {k: stats(v) for k, v in by_config[c].items()} for c in CONFIGS}
    delta = {
        k: f"{summary['with_skill'][k]['mean'] - summary['without_skill'][k]['mean']:+.2f}"
        for k in ("pass_rate", "time_seconds", "tokens")
    }
    summary["delta"] = delta

    benchmark = {
        "metadata": {
            "skill_name": "simplify-documentation",
            "skill_path": str(Path(__file__).resolve().parent.parent),
            "evals_run": sorted({r["eval_id"] for r in runs}),
            "runs_per_configuration": 1,
        },
        "runs": sorted(runs, key=lambda r: (r["eval_id"], r["configuration"] != "with_skill")),
        "run_summary": summary,
        "notes": [],
    }

    out = iteration / "benchmark.json"
    out.write_text(json.dumps(benchmark, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    for c in CONFIGS:
        pr = summary[c]["pass_rate"]
        print(f"  {c:14s} pass_rate {pr['mean']:.0%} ± {pr['stddev']:.2f}"
              f"   {summary[c]['time_seconds']['mean']:.0f}s   {summary[c]['tokens']['mean']:.0f} tok")
    print(f"  delta {delta}")


if __name__ == "__main__":
    main()
