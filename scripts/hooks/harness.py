"""Claude Code hooks of this repository, one subcommand per event. Configured in .claude/settings.json. Stdlib only.

    main-md     PostToolUse on Edit|Write: after an edit of main.md, run check_abbreviations.py, check.py and
                claim_quotes.py --check and hand their output to the model.
    shell-pre   PreToolUse on Bash: record size and mtime of notes.md, main.md and every file in raw/.
    shell-post  PostToolUse on Bash: compare with that record. A command that changed notes.md or the content of a
                file in raw/ is reported to the model as a block (the permission rules cover only Edit and Write, so a
                shell command is the way round them); a rename in raw/ is reported as a note; a changed main.md gets
                the same checks as main-md.
    stop        Stop: when wiki/, main.md or docs/claims-by-source.md has uncommitted changes, run check.py (and
                claim_quotes.py --check if main.md or the claims file changed); on an ERROR or a stale claims file,
                keep the agent working once, with the findings as the reason.

Every subcommand reads the hook payload from stdin and prints nothing when there is nothing to say. The shell hooks
detect a change after the fact; they do not prevent it.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = Path(tempfile.gettempdir()) / "claude-harness-hooks"


def run_script(script, *args):
    r = subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / script), *args], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8")
    return f"$ python -I scripts/{' '.join([script, *args])}\n{(r.stdout + r.stderr).strip()}"


def main_md_checks():
    return "\n\n".join(run_script(*cmd) for cmd in
                       (("check_abbreviations.py",), ("check.py",), ("claim_quotes.py", "--check")))


def emit(event, context=None, block_reason=None):
    out = {}
    if block_reason:
        out.update(decision="block", reason=block_reason)
    if context:
        out["hookSpecificOutput"] = {"hookEventName": event, "additionalContext": context}
    if out:
        print(json.dumps(out))


def snapshot():
    files = [ROOT / "notes.md", ROOT / "main.md"] + [p for p in (ROOT / "raw").rglob("*") if p.is_file()]
    return {p.relative_to(ROOT).as_posix(): [p.stat().st_size, p.stat().st_mtime_ns] for p in files if p.exists()}


def state_file(payload):
    return STATE_DIR / f"{payload.get('tool_use_id') or payload.get('session_id') or 'last'}.json"


def shell_pre(payload):
    STATE_DIR.mkdir(exist_ok=True)
    state_file(payload).write_text(json.dumps(snapshot()), encoding="utf-8")


def shell_post(payload):
    f = state_file(payload)
    if not f.exists():
        return
    before, after = json.loads(f.read_text(encoding="utf-8")), snapshot()
    f.unlink()
    changed = sorted(k for k in before.keys() & after.keys() if before[k] != after[k])
    gone, new = sorted(before.keys() - after.keys()), sorted(after.keys() - before.keys())
    renames = []
    for old in list(gone):  # a rename keeps size and mtime
        match = next((n for n in new if n.startswith("raw/") and after[n] == before[old]), None)
        if old.startswith("raw/") and match:
            renames.append(f"{old} -> {match}")
            gone.remove(old)
            new.remove(match)
    protected = [f"changed: {k}" for k in changed if k == "notes.md" or k.startswith("raw/")]
    protected += [f"deleted: {k}" for k in gone if k == "notes.md" or k.startswith("raw/")]
    protected += [f"created: {k}" for k in new if k == "notes.md"]
    context = []
    if renames:
        context.append("Renamed in raw/ by this command (allowed only when ingesting a source the researcher named): "
                       + "; ".join(renames))
    if "main.md" in changed:
        context.append("main.md was changed by a shell command, so the Edit hook did not run; its checks:\n\n"
                       + main_md_checks())
    reason = None
    if protected:
        reason = ("This shell command changed files that are off limits (AGENTS.md: notes.md is the researcher's, "
                  "raw/ is immutable): " + "; ".join(protected)
                  + ". Stop, tell the researcher exactly what changed, and do not repair it on your own "
                  "(git can restore a tracked file; a git-ignored PDF may need the researcher's copy).")
    emit("PostToolUse", "\n\n".join(context) or None, reason)


def stop(payload):
    if payload.get("stop_hook_active"):
        return
    r = subprocess.run(["git", "status", "--porcelain", "--", "wiki", "main.md", "docs/claims-by-source.md"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    dirty = [line[3:] for line in r.stdout.splitlines()]
    if not dirty:
        return
    problems = []
    check = subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "check.py")], cwd=ROOT,
                           capture_output=True, text=True, encoding="utf-8")
    problems += [line for line in check.stdout.splitlines() if line.startswith("ERROR")]
    if any(p in ("main.md", "docs/claims-by-source.md") for p in dirty):
        cq = run_script("claim_quotes.py", "--check")
        if "out of date" in cq:
            problems.append(cq.splitlines()[1])
    if problems:
        emit("Stop", block_reason="Finishing check (AGENTS.md): uncommitted changes in wiki/, main.md or the claims "
             "file, and the checks report:\n" + "\n".join(problems)
             + "\nFix these before finishing. If they are not from this task, say so to the researcher instead.")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    payload = json.load(sys.stdin)
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "main-md":
        if Path((payload.get("tool_input") or {}).get("file_path", "")).name == "main.md":
            emit("PostToolUse", main_md_checks())
    elif cmd == "shell-pre":
        shell_pre(payload)
    elif cmd == "shell-post":
        shell_post(payload)
    elif cmd == "stop":
        stop(payload)
    else:
        sys.exit(f"unknown subcommand {cmd!r}")


if __name__ == "__main__":
    main()
