#!/usr/bin/env python3
"""Deterministic consistency check for the wiki. Stdlib only; read-only, fixes nothing.

Run from anywhere: python -I scripts/check.py
Exit code 1 if any ERROR is found (warnings and info do not fail the run).

It cannot verify that author lists or findings are true (that needs the source itself),
but it catches structural ways a citation can appear without a source behind it. It also
reports where main.md has made a connection the wiki lacks (sources cited in one sentence
whose pages do not link each other) and wiki tags outside the vocabulary in AGENTS.md.
Two records of checks done by reading are looked for, not verified: the `Checks:` line of an
ingest log entry (ingest skill) and the `**Checked against source:**` line of a paper page
(`/grinding wiki`).
"""
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI, RAW, PAPERS = ROOT / "wiki", ROOT / "raw", ROOT / "wiki" / "papers"
LOG_TYPES = {"init", "ingest", "query", "draft", "lint", "grill"}
NON_PAGES = {"index.md", "log.md", "references.md"}
# Archives of the log written by scripts/rotate_log.py, in wiki/log-archive/: not wiki pages (no index entry, no tags).
LOG_DIR = WIKI / "log-archive"
LOG_ARCHIVE = re.compile(r"^log-\d{4}-\d{2}-\d{2}-to-\d{4}-\d{2}-\d{2}(?:-\d+)?\.md$")
LOG_LIMIT = 40_000  # bytes; keep in step with --limit in scripts/rotate_log.py


def non_page(p):
    return (p.parent == WIKI and p.name in NON_PAGES) or (p.parent == LOG_DIR and bool(LOG_ARCHIVE.match(p.name)))

findings = {"ERROR": [], "WARN": [], "INFO": []}


def report(level, where, msg):
    findings[level].append(f"{where}: {msg}")


def read(path):
    return path.read_text(encoding="utf-8")


def norm(surname):
    """'Mäki' / 'Weiser-Bitoun' / 'Van Ammel' -> 'maki' / 'weiserbitoun' / 'vanammel'."""
    s = unicodedata.normalize("NFKD", surname).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]", "", s.lower())


def rel(path):
    return path.relative_to(ROOT).as_posix()


# --- references.md: key (surname, year) -> DOI --------------------------------------
refs = {}
for line in read(WIKI / "references.md").splitlines():
    m = re.match(r"^([^\s,]+(?: [^\s,]+)?),[^(]*\((\d{4})(?:,[^)]*)?\)", line)
    if not m or line.startswith(("#", ">", "Default", "Auto-")):
        continue
    key = (norm(m.group(1)), m.group(2))
    doi = re.search(r"https://doi\.org/(\S+)", line)
    if key in refs:
        report("ERROR", "wiki/references.md", f"duplicate entry for {key[0]} {key[1]}")
    if not doi:
        report("WARN", "wiki/references.md", f"no DOI link: {line[:60]}…")
    refs[key] = doi.group(1).rstrip(".") if doi else None

# --- paper pages ---------------------------------------------------------------------
page_keys, raw_used = {}, set()
for page in sorted(PAPERS.glob("*.md")):
    text, where = read(page), rel(page)
    m = re.match(r"([a-z\-]+?)-(\d{4})-", page.name)
    if not m:
        report("WARN", where, "filename is not <firstauthor>-<year>-<keyword>.md")
        continue
    key = (norm(m.group(1)), m.group(2))
    page_keys[key] = page
    if key not in refs:
        report("ERROR", where, "no matching entry in wiki/references.md")
    f = re.search(r"\*\*File:\*\*\s*\[\[(raw/[^\]]+)\]\]", text)
    if not f:
        report("WARN", where, "no **File:** [[raw/...]] line (source PDF not recorded)")
    elif not (ROOT / f.group(1)).exists():
        report("ERROR", where, f"**File:** points to missing {f.group(1)}")
    else:
        raw_used.add(f.group(1))
        raw_stem = Path(f.group(1)).stem
        if not raw_stem.startswith(page.stem):
            report("WARN", where, f"raw file stem '{raw_stem}' differs from page stem '{page.stem}' (rename per the ingest skill)")
    # supplementary files linked anywhere on the page (e.g. a **Supplementary:** line) count as referenced
    raw_used.update(r for r in re.findall(r"\[\[(raw/[^\]|#]+)", text) if (ROOT / r).exists())
    # the first author on the page must be the surname the page and the reference are keyed on;
    # an author-order error once survived for weeks in the MEA review repository this template comes from
    a = re.search(r"^\*\*Authors:\*\*\s*([^,\n]+)", text, re.M)
    if a:
        first = a.group(1).replace("\\*", "").replace("*", "").strip()
        if norm(first.split()[-1]) != key[0] and norm(first) != key[0]:
            report("WARN", where, f"first author on the page ('{first}') does not match the page "
                                  f"and reference key '{key[0]}'; check the author order against the PDF")
    d = re.search(r"\*\*DOI:\*\*\s*(\S+)", text)
    if d and refs.get(key) and d.group(1).rstrip(".") != refs[key]:
        report("ERROR", where, f"DOI {d.group(1)} differs from references.md ({refs[key]})")
# --- paper pages checked against their source (/grinding wiki) ----------------------------
# The line is written when the researcher accepts a wiki grinding; the date is compared with the
# page's last commit, so a page edited in a later commit is listed again. One summary line for the
# pages never checked, so that the many pages ingested before the check existed do not flood the output.
import subprocess
last_commit = {}
try:
    git_log = subprocess.run(["git", "log", "--format=@%cs", "--name-only", "--", "wiki/papers"], cwd=ROOT,
                             capture_output=True, text=True, encoding="utf-8").stdout
    day = None
    for line in git_log.splitlines():
        if line.startswith("@"):
            day = line[1:]
        elif line.strip():
            last_commit.setdefault(line.strip(), day)
except OSError:
    pass
unchecked = []
for page in page_keys.values():
    c = re.search(r"^\*\*Checked against source:\*\*\s*(\d{4}-\d{2}-\d{2})", read(page), re.M)
    if not c:
        unchecked.append(page.stem)
    elif last_commit.get(rel(page), "") > c.group(1):
        report("INFO", rel(page), f"changed in a commit of {last_commit[rel(page)]}, after its check against the "
                                  f"source ({c.group(1)}); consider /grinding wiki again")
if unchecked:
    report("INFO", "wiki/papers", f"{len(unchecked)} of {len(page_keys)} pages not yet checked against their source "
                                  f"(/grinding wiki): {', '.join(sorted(unchecked))}")

for key in refs:
    if key not in page_keys:
        report("ERROR", "wiki/references.md", f"{key[0]} {key[1]} has no page in wiki/papers/")

for f in sorted(RAW.iterdir()):
    if f.is_file() and not f.name.startswith(".") and f"raw/{f.name}" not in raw_used:
        report("INFO", f"raw/{f.name}", "not referenced by any paper page (supplementary or not ingested)")

# --- index.md and orphans ------------------------------------------------------------
index_text = read(WIKI / "index.md")
indexed = set()
for target in re.findall(r"\]\(([^)#]+\.md)\)", index_text):
    path = (WIKI / target).resolve()
    indexed.add(path)
    if not path.exists():
        report("ERROR", "wiki/index.md", f"broken link {target}")
pages = [p for p in WIKI.rglob("*.md") if not non_page(p)]
for p in pages:
    if p.resolve() not in indexed:
        report("ERROR", rel(p), "not listed in wiki/index.md")

# --- broken relative links inside wiki pages -----------------------------------------
for p in WIKI.rglob("*.md"):
    for target in re.findall(r"\]\(([^)#\s]+)\)", read(p)):
        if target.startswith(("http", "mailto:")):
            continue
        if not (p.parent / target).exists():
            report("ERROR", rel(p), f"broken link {target}")

# --- main.md citations must exist in references.md -----------------------------------
main = read(ROOT / "main.md")
cited = set()
for group in re.findall(r"\(([^()]*\d{4}[a-z]?[^()]*)\)", main):
    for part in group.split(";"):
        m = re.match(r"\s*([A-ZÄÖÅ][\w\-äöåÄÖÅ]+)(?:,?\s+(?:et al\.|and\s+[A-ZÄÖÅ][\w\-]+|&\s+[A-ZÄÖÅ][\w\-]+))?,?\s+((?:19|20)\d{2})[a-z]?\s*$", part)
        if m:
            cited.add((norm(m.group(1)), m.group(2)))
for m in re.finditer(r"([A-ZÄÖÅ][\w\-äöåÄÖÅ]+)(?:\s+et al\.|\s+and\s+[A-ZÄÖÅ][\w\-]+)?\s+\(((?:19|20)\d{2})[a-z]?\)", main):
    cited.add((norm(m.group(1)), m.group(2)))
for key in sorted(cited - set(refs)):
    report("ERROR", "main.md", f"cites {key[0]} {key[1]}, which is not in wiki/references.md")
for key in sorted(set(refs) - cited):
    report("INFO", "wiki/references.md", f"{key[0]} {key[1]} is not cited in main.md")
# the reference list at the end of main.md must hold exactly the cited entries, verbatim from wiki/references.md
ref_lines = [l for l in read(WIKI / "references.md").split("\n---\n", 1)[-1].splitlines() if l.strip()]
parts = re.split(r"^# References[ \t]*$", main, maxsplit=1, flags=re.M)
if len(parts) < 2:
    report("WARN", "main.md", "no '# References' heading; the reference list cannot be compared with wiki/references.md")
main_lines = [l for l in parts[-1].splitlines() if l.strip() and not l.lstrip().startswith("<!--")] if len(parts) == 2 else []
main_keys = set()
for l in main_lines:
    if l not in ref_lines:
        report("ERROR", "main.md", f"reference differs from wiki/references.md: {l[:70]}…")
    m = re.match(r"^([^\s,]+(?: [^\s,]+)?),[^(]*\((\d{4})(?:,[^)]*)?\)", l)
    if m:
        main_keys.add((norm(m.group(1)), m.group(2)))
for key in sorted(cited - main_keys):
    report("ERROR", "main.md", f"{key[0]} {key[1]} is cited in the text but missing from the # References list")
for key in sorted(main_keys - cited):
    report("WARN", "main.md", f"{key[0]} {key[1]} is in the # References list but not cited in the text")
if "[CITATION NEEDED]" in main:
    report("INFO", "main.md", f"{main.count('[CITATION NEEDED]')} open [CITATION NEEDED] flag(s)")

# --- write-back from main.md to the wiki ---------------------------------------------
# main.md compares sources and gathers themes; the wiki should carry the same connections.
# (1) Sources cited in one sentence of main.md should have linked wiki pages (INFO).
#     The "Limitations of this review" section is skipped: it lists sources as examples.
def cite_keys(text):
    keys = set()
    for group in re.findall(r"\(([^()]*\d{4}[a-z]?[^()]*)\)", text):
        for part in group.split(";"):
            m = re.match(r"\s*([A-ZÄÖÅ][\w\-äöåÄÖÅ]+)(?:,?\s+(?:et al\.|and\s+[A-ZÄÖÅ][\w\-]+|&\s+[A-ZÄÖÅ][\w\-]+))?,?\s+((?:19|20)\d{2})[a-z]?\s*$", part)
            if m:
                keys.add((norm(m.group(1)), m.group(2)))
    for m in re.finditer(r"([A-ZÄÖÅ][\w\-äöåÄÖÅ]+)(?:\s+et al\.|\s+and\s+[A-ZÄÖÅ][\w\-]+)?\s+\(((?:19|20)\d{2})[a-z]?\)", text):
        keys.add((norm(m.group(1)), m.group(2)))
    return {k for k in keys if k in page_keys}


body = re.split(r"^# References[ \t]*$", main, maxsplit=1, flags=re.M)[0]
body = re.sub(r"^# Limitations of this review.*?(?=^# )", "", body, flags=re.M | re.S)
# A pair counts as connected if one paper page links the other, or if a concept page
# (outside wiki/papers/) links both: list-like sentences ("used in A, B and C") belong on a hub page.
stem_key = {p.stem: k for k, p in page_keys.items()}
def paper_links(path):
    return {stem_key[t] for t in re.findall(r"\[\[wiki/papers/([^\]|#]+?)(?:\.md)?\]\]", read(path)) if t in stem_key}
linked = set()
for key, page in page_keys.items():
    linked.update(frozenset((key, k2)) for k2 in paper_links(page) if k2 != key)
for p in WIKI.glob("*.md"):
    if not non_page(p):
        hub = sorted(paper_links(p))
        linked.update(frozenset((a, b)) for i, a in enumerate(hub) for b in hub[i + 1:])
unlinked = {}
for line in body.splitlines():
    for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z*])", line):
        keys = sorted(cite_keys(sentence))
        for i, a in enumerate(keys):
            for b in keys[i + 1:]:
                if frozenset((a, b)) not in linked:
                    unlinked[(a, b)] = unlinked.get((a, b), 0) + 1
for (a, b), n in sorted(unlinked.items()):
    report("INFO", "main.md", f"{page_keys[a].stem} and {page_keys[b].stem} are cited in the same sentence "
           f"({n}x) but their wiki pages do not link each other (write back, draft skill step 5)")

# (2) Tags come from the vocabulary in AGENTS.md ("Tag vocabulary"), so the graph groups by theme (WARN).
agents = ROOT / "AGENTS.md"
vocab_line = next((l for l in read(agents).splitlines() if l.lstrip("- ").startswith("**Tag vocabulary.**")), "") if agents.exists() else ""
vocab = {t for t in re.findall(r"`([a-z0-9/\-]+)`", vocab_line) if not t.endswith("/")}
if vocab:
    for p in sorted(WIKI.rglob("*.md")):
        if non_page(p):
            continue
        fm = re.match(r"---\r?\ntags:\s*\[([^\]]*)\]", read(p))
        tags = [t.strip() for t in fm.group(1).split(",") if t.strip()] if fm else []
        if not tags:
            report("WARN", rel(p), "no tags in the front matter (see Tag vocabulary in AGENTS.md)")
        for t in tags:
            if t not in vocab:
                report("WARN", rel(p), f"tag '{t}' is not in the Tag vocabulary of AGENTS.md")

# --- log.md header format ------------------------------------------------------------
if (WIKI / "log.md").stat().st_size > LOG_LIMIT:
    report("WARN", "wiki/log.md", f"{(WIKI / 'log.md').stat().st_size} bytes, over {LOG_LIMIT}: "
                                  "run python -I scripts/rotate_log.py --write to move the oldest entries to archives")
LOG_FILES = [WIKI / "log.md"] + sorted(p for p in LOG_DIR.glob("log-*.md") if LOG_ARCHIVE.match(p.name))
for log_path in LOG_FILES:
    if not log_path.exists():
        continue
    for i, line in enumerate(read(log_path).splitlines(), 1):
        if line.startswith("## [") and "YYYY" not in line:
            m = re.match(r"## \[\d{4}-\d{2}-\d{2}\] (\w+) \| .+", line)
            if not m or m.group(1) not in LOG_TYPES:
                report("WARN", f"{rel(log_path)}:{i}", f"non-standard log header: {line[:60]}")

# An ingest entry records what was actually read (ingest skill, step 9): a line starting "Checks:"
# naming the full text, figures, supplements, authors and dates. Required from INGEST_CHECKS_FROM on.
INGEST_CHECKS_FROM = "2026-11-25"
INGEST_CHECK_WORDS = ("full text", "figures", "supplements", "authors", "dates")
for log_path in LOG_FILES:
    if not log_path.exists():
        continue
    for entry in re.split(r"^(?=## \[)", read(log_path), flags=re.M):
        m = re.match(r"## \[(\d{4}-\d{2}-\d{2})\] ingest \|(.*)", entry)
        if not m or m.group(1) < INGEST_CHECKS_FROM:
            continue
        checks = re.search(r"^\W*Checks:(.*)$", entry, re.M)
        missing = [w for w in INGEST_CHECK_WORDS if not checks or w not in checks.group(1).lower()]
        if missing:
            report("WARN", rel(log_path), f"ingest entry of {m.group(1)} ({m.group(2).strip()[:40]}) has no Checks: line "
                                          f"naming {', '.join(missing)} (ingest skill, step 9)")

# --- docs/lessons.md: every lesson traceable to the log --------------------------------
# A lesson cites its evidence as "log <date> <type>", which must match a "## [<date>] <type> |"
# header in wiki/log.md or one of its archives; the date-and-type form survives log rotation.
LESSONS = ROOT / "docs" / "lessons.md"
if LESSONS.exists():
    headers = set()
    for log_path in LOG_FILES:
        headers.update(re.findall(r"^## \[(\d{4}-\d{2}-\d{2})\] (\w+) \|", read(log_path), re.M))
    for n, line in enumerate(read(LESSONS).splitlines(), 1):
        for d, kind in re.findall(r"\blog (\d{4}-\d{2}-\d{2}) (\w+)\b", line):
            if (d, kind) not in headers:
                report("WARN", f"docs/lessons.md:{n}", f"evidence 'log {d} {kind}' matches no entry in wiki/log.md or wiki/log-archive/")

# --- figures: the rendered images against their Mermaid source -------------------------
# The ```mermaid blocks in main.md are the source of truth (claim_quotes.py quotes from them).
# scripts/figures.py copies each to figures/*.mmd and records its hash; a stale image is the kind
# of error nobody notices, so the hash is compared here. This repeats the fence scan of figures.py
# in a few lines; keep the two in step if the fence or caption format changes.
FIG_DIR = ROOT / "figures"
manifest_path = FIG_DIR / "figures.json"
if manifest_path.exists():
    import hashlib
    import json

    manifest = json.loads(read(manifest_path))
    by_caption, main_lines = {}, read(ROOT / "main.md").split("\n")
    i = 0
    while i < len(main_lines):
        if main_lines[i].strip().startswith("```mermaid"):
            start = i
            i += 1
            while i < len(main_lines) and not main_lines[i].strip().startswith("```"):
                i += 1
            body = "\n".join(main_lines[start + 1:i])
            number = None
            for back in range(start - 1, max(start - 6, -1), -1):
                m = re.match(r"^\*Figure (\d+)\.", main_lines[back].strip())
                if m:
                    number = int(m.group(1))
                    break
            by_caption[number] = hashlib.sha256(body.encode("utf-8")).hexdigest()
        i += 1
    for slug, entry in manifest.items():
        image = FIG_DIR / entry.get("image", slug + ".svg")
        current = by_caption.get(entry.get("figure"))
        if current is None:
            report("WARN", f"figures/{slug}", "no ```mermaid block in main.md matches this figure number")
        elif current != entry.get("sha256"):
            report("WARN", f"figures/{slug}", "the diagram in main.md changed since this image was recorded; "
                                              "re-render it with python -I scripts/figures.py --render")
        if not image.exists():
            report("WARN", rel(image), "rendered image missing; render it with python -I scripts/figures.py --render")

# --- register of own inferences: the Support vocabulary --------------------------------
# Every **Support:** line of docs/claims-by-source.md names where a statement's warrant comes
# from, with a value from the fixed list defined in that file's reading guide. The values grew
# past the guide once before, so the list is checked here; extend it in the guide, then here.
SUPPORT_VALUES = {"sourced", "thin", "inference", "opinion", "none", "inherited"}
CLAIMS = ROOT / "docs" / "claims-by-source.md"
if CLAIMS.exists():
    for n, line in enumerate(read(CLAIMS).splitlines(), 1):
        m = re.match(r"\s*- \*\*Support:\*\* (.+)", line)
        if not m:
            continue
        used = set(re.findall(r"`([a-z]+)`", m.group(1)))
        unknown = used - SUPPORT_VALUES
        if unknown:
            report("WARN", f"{rel(CLAIMS)}:{n}",
                   f"support value(s) outside the vocabulary: {', '.join(sorted(unknown))}")
        elif not used:
            report("WARN", f"{rel(CLAIMS)}:{n}",
                   "no support value; use one of " + ", ".join(sorted(SUPPORT_VALUES)))

# --- claims file: no number used twice within a section ---------------------------------
# Claims are cited by number ("Smith (4)", "register item 35"), so a duplicate makes a
# reference ambiguous. In the MEA review repository one slipped in and was found only by eye.
if CLAIMS.exists():
    section, seen = None, {}
    for n, line in enumerate(read(CLAIMS).splitlines(), 1):
        if line.startswith("## "):
            section, seen = line[3:].replace("✅", "").strip(), {}
            continue
        m = re.match(r"- \[[ xX]\] (?:\((\w+)\)|\*\*(\w+)\.)", line)
        if not m or section is None:
            continue
        num = m.group(1) or m.group(2)
        if num in seen:
            report("WARN", f"{rel(CLAIMS)}:{n}", f"number {num} is used twice in '{section}' "
                                                f"(first on line {seen[num]})")
        else:
            seen[num] = n

# --- Highlights: the 85-character convention --------------------------------------------
# Journals that ask for highlights (Elsevier among them) cap each at 85 characters with spaces.
# A preprint has no hard limit, so a longer line is reported as INFO, not as a warning.
HIGHLIGHT_MAX = 85
hl = re.search(r"^# Highlights[ \t]*\n(.*?)(?=^# )", main, re.M | re.S)
if hl:
    for line in hl.group(1).splitlines():
        if line.startswith("- ") and len(line) - 2 > HIGHLIGHT_MAX:
            report("INFO", "main.md", f"highlight is {len(line) - 2} characters (convention {HIGHLIGHT_MAX}): {line[2:50]}…")

# --- accidental Obsidian tags ----------------------------------------------------------
# A '#word' in prose is read as a tag in Obsidian. Tags belong in the front matter only.
# Always escape the hash with a backslash (\#word); quotes do not count as an escape.
TAG = re.compile(r"(?<![\w\\&/#`])#(?=[A-Za-z_])[\w/-]*[A-Za-z_][\w/-]*")
for p in [ROOT / "main.md", *sorted(WIKI.rglob("*.md")), *sorted((ROOT / "docs").glob("*.md"))]:
    in_front, in_fence = False, False
    for n, line in enumerate(read(p).splitlines(), 1):
        s = line.strip()
        if n == 1 and s == "---":
            in_front = True
            continue
        if in_front:
            in_front = s != "---"
            continue
        if s.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or s.startswith("#"):
            continue
        for m in TAG.finditer(re.sub(r"`[^`]*`|https?://\S+", "", line)):
            report("WARN", f"{rel(p)}:{n}", f"'{m.group(0)}' would be read as an Obsidian tag; escape the hash with a backslash")

# --- output --------------------------------------------------------------------------
sys.stdout.reconfigure(encoding="utf-8")
for level in ("ERROR", "WARN", "INFO"):
    for item in findings[level]:
        print(f"{level:5} {item}")
print(f"\n{len(findings['ERROR'])} error(s), {len(findings['WARN'])} warning(s), {len(findings['INFO'])} info "
      f"— {len(page_keys)} paper pages, {len(refs)} references, {len(cited)} distinct citations in main.md")
sys.exit(1 if findings["ERROR"] else 0)
