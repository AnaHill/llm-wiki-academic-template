#!/usr/bin/env python3
"""Check that each task loads the right skill, by running headless Claude Code sessions. Stdlib only.

Run it after changing AGENTS.md or a skill's description: a skill whose description no longer matches its task
fails silently, because the agent then works from AGENTS.md alone. Each case sends one prompt to
`claude -p` in plan mode (no file can be changed) and looks in the transcript for the skill being loaded,
either through the Skill tool or by reading `.claude/skills/<name>/SKILL.md` (as an agent without skill
support does, following the table in AGENTS.md). One case disables skills to check that path.

    python -I scripts/eval_skills.py            # list the cases and the command, run nothing
    python -I scripts/eval_skills.py --run      # run all cases in parallel (costs API usage, about USD 2)
    python -I scripts/eval_skills.py --run --only ingest,query --model sonnet

Exit code 1 if any case fails. Transcripts are kept in a temporary folder whose path is printed.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASK_SKILLS = {"ingest", "draft", "lint"}

# name: (prompt, expected skill or None for "no task skill", extra CLI arguments)
CASES = {
    "ingest": ("I added a new PDF to raw/ (no name yet). List briefly the steps you take to process it. "
               "Do not change any files.", "ingest", []),
    "draft": ("Suggest a tighter first sentence for the Abstract of main.md and say what else would have to be "
              "done if the change were made. Do not save anything.", "draft", []),
    "lint": ("Run a health check of the wiki. A short report of the five most important findings is enough. "
             "Do not change anything.", "lint", []),
    "query": ("What sources does the wiki have so far, and what do they cover? "
              "One short paragraph with sources.", None, []),
    "ingest-no-skills": ("I added a new PDF to raw/ (no name yet). List briefly the steps you take to process it. "
                         "Do not change any files.", "ingest", ["--disable-slash-commands"]),
}


def command(prompt, extra, model):
    cmd = ["claude", "-p", prompt, "--permission-mode", "plan", "--max-turns", "8",
           "--output-format", "stream-json", "--verbose", *extra]
    return cmd + (["--model", model] if model else [])


def skills_loaded(transcript):
    loaded = set()
    for line in transcript.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "assistant":
            continue
        for block in event["message"].get("content", []):
            if block.get("type") != "tool_use":
                continue
            args = block.get("input") or {}
            if block["name"] == "Skill":
                loaded.add(args.get("skill", ""))
            path = str(args.get("file_path", "")).replace("\\", "/")
            if "/.claude/skills/" in path and path.endswith("/SKILL.md"):
                loaded.add(path.split("/.claude/skills/")[1].split("/")[0])
    return loaded


def run_case(name, model, out_dir):
    prompt, expected, extra = CASES[name]
    r = subprocess.run(command(prompt, extra, model), cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    (out_dir / f"{name}.jsonl").write_text(r.stdout, encoding="utf-8")
    loaded = skills_loaded(r.stdout)
    ok = expected in loaded if expected else not (loaded & TASK_SKILLS)
    return name, ok, expected or "(none)", sorted(loaded) or ["(none)"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", action="store_true", help="run the cases (without it, only list them)")
    ap.add_argument("--only", help="comma-separated case names")
    ap.add_argument("--model", help="model alias or id passed to claude --model")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    names = args.only.split(",") if args.only else list(CASES)
    unknown = [n for n in names if n not in CASES]
    if unknown:
        sys.exit(f"unknown case(s): {', '.join(unknown)}; known: {', '.join(CASES)}")
    if not args.run:
        for n in names:
            print(f"{n:18} expects {CASES[n][1] or '(no task skill)'}: {CASES[n][0]}")
        print("\nDry run; add --run to execute (costs API usage).")
        return
    out_dir = Path(tempfile.mkdtemp(prefix="eval-skills-"))
    with ThreadPoolExecutor(len(names)) as pool:
        results = list(pool.map(lambda n: run_case(n, args.model, out_dir), names))
    for name, ok, expected, loaded in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name:18} expected {expected:10} loaded {', '.join(loaded)}")
    print(f"\nTranscripts: {out_dir}")
    sys.exit(0 if all(ok for _, ok, *_ in results) else 1)


if __name__ == "__main__":
    main()
