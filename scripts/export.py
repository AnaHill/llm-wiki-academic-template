#!/usr/bin/env python3
"""Build `main-export.md`, the copy of the paper that the HTML and the PDF are made from. Stdlib only.

`main.md` is written for the wiki workflow: the figures are ```mermaid blocks that claim_quotes.py
reads as sentences of the draft, the front matter is metadata rather than a visible title page, and
the reference list carries bare DOI URLs. None of that survives a Markdown-to-HTML converter well.
This script writes a separate build copy, so `main.md` keeps working as the draft:

  1. the Mermaid diagrams become image references to the rendered figures/*.svg, with alt text from
     the figure caption, so the HTML carries pictures instead of drawing them in the reader's
     browser from an unpinned CDN, and the PDF cannot split a diagram across pages;
  2. a visible title block is written from the front matter, which converters otherwise drop, so the
     title, the author and the date appear on the first page;
  3. bare URLs become Markdown links, so the DOIs in the reference list are clickable;
  4. HTML comments are removed, so nothing invisible travels into the published HTML source.

The front matter is kept as well: a converter that reads it gets the document title, and one that
does not drops it silently, as the test export did.

Usage (run from the repository root):
    python -I scripts/export.py             dry run: report what would change, write nothing
    python -I scripts/export.py --write     write main-export.md
    python -I scripts/export.py --write --date 2026-11-25     a date other than today

`main-export.md` is generated and git-ignored: never edit it, edit `main.md` and build again.
"""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "main.md"
TARGET = ROOT / "main-export.md"
MANIFEST = ROOT / "figures" / "figures.json"

CAPTION = re.compile(r"^\*Figure (\d+)\.")
# A bare URL: not already the target of a Markdown link, and without the sentence punctuation that
# usually follows it. Parentheses are excluded so that "(see https://x)" does not swallow the ")".
URL = re.compile(r"(?<![(\[])\bhttps?://[^\s<>()\[\]]+[^\s<>()\[\].,;:]")
LINK = re.compile(r"\[[^\]]*\]\([^)]*\)")


def split_front_matter(text):
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end == -1:
        return "", text
    return text[:end + 4], text[end + 4:].lstrip("\n")


def front_matter_field(front, name):
    m = re.search(rf"^{name}:\s*(.+?)\s*$", front, re.M)
    if not m:
        return ""
    return m.group(1).strip().strip('"').strip("'")


def title_block(front, date):
    """The visible heading that converters do not make from the front matter."""
    title = front_matter_field(front, "title")
    author = front_matter_field(front, "author")
    lines = []
    if title:
        lines.append(f"# {title}")
    if author:
        lines.append("")
        lines.append(f"**{author}**")
    lines.append("")
    lines.append(f"*{date}*")
    return "\n".join(lines)


def replace_diagrams(lines, figures):
    """Swap each ```mermaid fence for an image reference; returns the new lines and how many."""
    out, used, i = [], 0, 0
    while i < len(lines):
        if lines[i].strip().startswith("```mermaid"):
            start = i
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                i += 1
            number = None
            for back in range(start - 1, max(start - 6, -1), -1):
                m = CAPTION.match(lines[back].strip())
                if m:
                    number = int(m.group(1))
                    break
            entry = figures.get(number)
            if entry:
                alt = entry["caption"].replace("[", "(").replace("]", ")")
                out.append(f"![{alt}](figures/{entry['image']})")
                used += 1
            else:
                out.extend(lines[start:i + 1])
                print(f"    no figure entry for the block at line {start + 1}; it was left as Mermaid")
            i += 1
            continue
        out.append(lines[i])
        i += 1
    return out, used


def linkify(text):
    """Make bare URLs clickable, leaving existing Markdown links and fenced code alone."""
    out, count, fenced = [], 0, False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            out.append(line)
            continue
        if fenced or "http" not in line:
            out.append(line)
            continue
        masked, spans = line, []
        for m in LINK.finditer(line):
            spans.append(m.group(0))
            masked = masked.replace(m.group(0), f"\x00{len(spans) - 1}\x00", 1)

        def wrap(m):
            nonlocal count
            count += 1
            return f"[{m.group(0)}]({m.group(0)})"

        masked = URL.sub(wrap, masked)
        for n, span in enumerate(spans):
            masked = masked.replace(f"\x00{n}\x00", span)
        out.append(masked)
    return "\n".join(out), count


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write", action="store_true", help="write main-export.md (default: dry run)")
    parser.add_argument("--date", default=datetime.date.today().isoformat(), help="date for the title block")
    args = parser.parse_args()

    text = MAIN.read_text(encoding="utf-8")
    front, body = split_front_matter(text)

    figures = {}
    if MANIFEST.exists():
        for entry in json.loads(MANIFEST.read_text(encoding="utf-8")).values():
            figures[entry["figure"]] = entry
    missing = [e["image"] for e in figures.values() if not (ROOT / "figures" / e["image"]).exists()]

    body, comments = re.subn(r"<!--.*?-->\n?", "", body, flags=re.S)
    lines, diagrams = replace_diagrams(body.split("\n"), figures)
    body, urls = linkify("\n".join(lines))

    heading = title_block(front, args.date)
    result = f"{front}\n\n{heading}\n\n{body}" if front else f"{heading}\n\n{body}"

    print(f"diagrams replaced by images: {diagrams}")
    print(f"bare URLs made clickable:    {urls}")
    print(f"HTML comments removed:       {comments}")
    print(f"title block:                 {'yes' if heading.startswith('#') else 'no title in front matter'}")
    if missing:
        print("\nthe rendered image is missing for: " + ", ".join(missing))
        print("render it with python -I scripts/figures.py --render before building the HTML")

    if args.write:
        TARGET.write_text(result.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
        print(f"\nwrote {TARGET.relative_to(ROOT).as_posix()}")
    else:
        print("\ndry run: nothing written")


main()
