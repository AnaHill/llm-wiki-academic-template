"""PostToolUse hook: after an Edit or Write of main.md, run the abbreviation and consistency checks.

Reads the hook payload from stdin and, when the edited file is main.md, runs
scripts/check_abbreviations.py, scripts/check.py and scripts/claim_quotes.py --check (whether the
claims file is out of date, and its Notes) and hands their output back to the model as additional context. Any other file is ignored. Configured in .claude/settings.json.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    payload = json.load(sys.stdin)
    path = (payload.get("tool_input") or {}).get("file_path", "")
    if Path(path).name != "main.md":
        return
    out = []
    for script, *args in (("check_abbreviations.py",), ("check.py",), ("claim_quotes.py", "--check")):
        r = subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / script), *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        out.append(f"$ python -I scripts/{' '.join([script, *args])}\n{(r.stdout + r.stderr).strip()}")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "\n\n".join(out)}}))


if __name__ == "__main__":
    main()
