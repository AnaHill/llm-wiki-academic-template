#!/usr/bin/env python3
"""Keep the Mermaid diagrams of main.md and their rendered images in step. Stdlib only.

The fenced ```mermaid blocks in `main.md` are the source of truth and stay there: `claim_quotes.py`
reads them as sentences of the draft, so 18 Timeline claims and the Figure 2 claims in
`docs/claims-by-source.md` are quoted from inside those blocks. Removing them would leave those
claims with no sentence to point at. What this script does instead is make the blocks usable
outside `main.md`:

  * `--write` copies each block to `figures/<slug>.mmd` and records its SHA-256 in
    `figures/figures.json`. `check.py` compares that hash with the current block and warns when a
    rendered image is older than the diagram it was made from.
  * `--render` does the same and also draws each block to `figures/<slug>.svg`, with a pinned
    Mermaid (MERMAID_URL) in headless Edge or Chrome. Mermaid Live is not used: its SVG export saved
    the preview pane as shown (dark site theme, pan-zoom scaling, no viewBox) whatever the Config
    tab said, which gave an image too small to read in the HTML and the PDF.
`scripts/export.py` reads that manifest when it builds `main-export.md`, the copy of the paper in
which the diagrams are replaced by the rendered images.

Usage (run from the repository root):
    python -I scripts/figures.py             dry run: report the figures found and their state
    python -I scripts/figures.py --write     write figures/*.mmd and figures/figures.json
    python -I scripts/figures.py --render    as --write, and render figures/*.svg
                                             (--browser PATH if Edge or Chrome is not found)

Rendering needs network access once per run to load Mermaid from jsDelivr; the diagram text is
not sent anywhere, it is drawn in the local browser.

The .mmd files are generated, like the `- >` lines of the claims file: edit the block in `main.md`
and run `--write` again, never the other way round.
"""
import argparse
import base64
import hashlib
import html
import json
import re
import subprocess
import sys
import tempfile
import xml.dom.minidom
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "main.md"
FIGURES = ROOT / "figures"
MANIFEST = FIGURES / "figures.json"
IMAGE_SUFFIX = ".svg"

# Figure number -> file stem. A figure without an entry falls back to "figN" and is reported,
# so a new diagram is named deliberately rather than by an accident of its caption wording.
NAMES = {}  # e.g. {1: "fig1-timeline", 2: "fig2-pipeline"}

# Pinned, so the same block always gives the same picture. Change deliberately and re-render both.
MERMAID_URL = "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js"
MERMAID_CONFIG = {
    "startOnLoad": False,
    "theme": "default",          # light; "neutral" was tried and made the timeline harder to read
    "look": "classic",
    "fontFamily": "Arial, Helvetica, sans-serif",
    "flowchart": {"htmlLabels": False},
    # The timeline colours its sections from a cycle of 12 scales; with the default theme some
    # sections (2022, 2025) got white text on light purple, which nearly vanishes in print
    # (found in the first PDF of the MEA review). Black labels on every scale.
    "themeVariables": {f"cScaleLabel{i}": "#000000" for i in range(12)},
    "securityLevel": "strict",
}
BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/microsoft-edge",
]
RENDER_PAGE = """<!doctype html><meta charset="utf-8"><body><div id="out">PENDING</div>
<script src="%s"></script>
<script>
(async () => {
  const out = document.getElementById('out');
  try {
    mermaid.initialize(%s);
    const { svg } = await mermaid.render('fig', %s);
    const bytes = new TextEncoder().encode(svg);
    let bin = ''; bytes.forEach(b => bin += String.fromCharCode(b));
    out.textContent = 'OK:' + btoa(bin);
  } catch (e) { out.textContent = 'ERR:' + e; }
})();
</script>"""

CAPTION = re.compile(r"^\*Figure (\d+)\.\s*(.+?)\*$")


def find_blocks(lines):
    """Return [(figure number, slug, caption, body, first line, last line)] for the mermaid fences.

    The caption is the nearest `*Figure N. ...*` line above the fence. check.py repeats this
    scan in a few lines of its own; keep the two in step if the fence or caption format changes.
    """
    out, i = [], 0
    while i < len(lines):
        if lines[i].strip().startswith("```mermaid"):
            start = i
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                i += 1
            body = "\n".join(lines[start + 1:i])
            number, caption = None, ""
            for back in range(start - 1, max(start - 6, -1), -1):
                m = CAPTION.match(lines[back].strip())
                if m:
                    number, caption = int(m.group(1)), m.group(2).strip()
                    break
            slug = NAMES.get(number, f"fig{number}" if number else f"figure-{len(out) + 1}")
            out.append((number, slug, caption, body, start, i))
        i += 1
    return out


def digest(body):
    return hashlib.sha256(body.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def find_browser(given):
    for candidate in ([given] if given else BROWSERS):
        if candidate and Path(candidate).exists():
            return candidate
    sys.exit("no Edge or Chrome found; pass --browser PATH")


def render(body, out, browser, tmp):
    """Draw one diagram to an SVG file with the pinned Mermaid in a headless browser."""
    # main.md keeps a literal \n in the Figure 2 labels (claim_quotes.py strips it when it reads
    # the block), but Mermaid 11 prints it as text. Break the line in the rendered copy only.
    source = body.replace("\\n", "<br/>")
    page = tmp / (out.stem + ".html")
    page.write_text(RENDER_PAGE % (MERMAID_URL, json.dumps(MERMAID_CONFIG), json.dumps(source)),
                    encoding="utf-8")
    dom = subprocess.run(
        [browser, "--headless=new", "--disable-gpu", f"--user-data-dir={tmp / 'profile'}",
         "--virtual-time-budget=15000", "--dump-dom", page.as_uri()],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180,
    ).stdout
    m = re.search(r'<div id="out">(.*?)</div>', dom, re.S)
    result = html.unescape(m.group(1)) if m else "no output from the browser"
    if not result.startswith("OK:"):
        sys.exit(f"{out.name}: rendering failed: {result[:300]}"
                 + (" (is the network up? Mermaid loads from jsDelivr)" if "PENDING" in result else ""))
    svg = base64.b64decode(result[3:]).decode("utf-8")
    # A line break makes Mermaid fall back to HTML labels, serialised with an unclosed <br>; that
    # is not XML, and an SVG loaded through <img> then shows nothing at all.
    svg = '<?xml version="1.0" encoding="UTF-8"?>\n' + re.sub(r"<br\s*>", "<br/>", svg) + "\n"
    xml.dom.minidom.parseString(svg.encode("utf-8"))
    out.write_text(svg, encoding="utf-8", newline="\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write", action="store_true", help="write figures/*.mmd and figures/figures.json")
    parser.add_argument("--render", action="store_true", help="as --write, and render figures/*.svg")
    parser.add_argument("--browser", help="path to Edge or Chrome, if not found automatically")
    args = parser.parse_args()

    lines = MAIN.read_text(encoding="utf-8").split("\n")
    blocks = find_blocks(lines)
    if not blocks:
        print("no ```mermaid block found in main.md")
        return

    manifest = {}
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    for number, slug, caption, body, start, _ in blocks:
        sha = digest(body)
        known = manifest.get(slug, {})
        image = FIGURES / (slug + IMAGE_SUFFIX)
        state = "image missing" if not image.exists() else (
            "image may be stale (the block changed)" if known.get("sha256") not in (None, sha) else "up to date")
        print(f"Figure {number} [{slug}] line {start + 1}: {len(body.splitlines())} lines, {state}")
        if number is None:
            print("    no '*Figure N. ...*' caption found above the block; it was named by position")
        elif number not in NAMES:
            print(f"    no name for figure {number} in NAMES; add one to scripts/figures.py")

    if args.render:
        browser = find_browser(args.browser)
        FIGURES.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            for number, slug, caption, body, _, _ in blocks:
                render(body, FIGURES / (slug + IMAGE_SUFFIX), browser, Path(tmp))
                print(f"rendered figures/{slug}{IMAGE_SUFFIX}")

    if args.write or args.render:
        FIGURES.mkdir(exist_ok=True)
        for number, slug, caption, body, _, _ in blocks:
            (FIGURES / (slug + ".mmd")).write_text(body + "\n", encoding="utf-8", newline="\n")
            manifest[slug] = {"figure": number, "caption": caption, "sha256": digest(body),
                              "image": slug + IMAGE_SUFFIX}
        MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8", newline="\n")
        print(f"\nwrote {len(blocks)} .mmd file(s) and {MANIFEST.relative_to(ROOT).as_posix()}")


main()
