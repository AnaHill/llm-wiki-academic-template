"""Check the abbreviations of main.md against its "# Abbreviations" list.

The list is a Markdown bullet list under a "# Abbreviations" heading, one entry per line; several
abbreviations may share a line:
    - **MEA**: multielectrode array
    - **APD50**, **APD90**: action potential duration at 50% and 90% repolarization
Reports
    WARN  an abbreviation-like token in the text that is not in the list (and not in IGNORE below)
    WARN  a listed abbreviation whose first use in the prose is not spelled out, i.e. not written as
          "long form (ABBR)" or "ABBR = long form" / "ABBR is ..."
    INFO  a listed abbreviation that does not occur in the text
The text is everything from "# Abstract" to "# References", without URLs and the Abbreviations list itself.
Usage counts the Highlights, tables and diagrams; the first-use check looks at the running prose only.
Plurals and compounds are folded: "MEAs" and "MEA-derived" count as "MEA".
Run from the repository root:  python -I scripts/check_abbreviations.py
"""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

# Tokens that look like abbreviations but are names (tools, databases, genes, mutations, licences, intervals, Mermaid keywords).
IGNORE = {
    # e.g. "MATLAB", "PubMed", "KCNH2" -- add the names your paper uses
}
SUFFIXES = ("s", "-like", "-based", "-derived", "-assisted", "-end")
TOKEN = re.compile(r"\b(?:\d[A-Z]|[a-z]{0,6}[A-Z][A-Za-z0-9]*[A-Z0-9][A-Za-z0-9\-]*)\b")


def section(text, title):
    m = re.search(r"^# " + re.escape(title) + r"[ \t]*\n(.*?)(?=^# |\Z)", text, flags=re.M | re.S)
    return m.group(1) if m else None


def fold(token, listed):
    if token in listed:
        return token
    for suf in SUFFIXES:
        if token.endswith(suf) and token[: -len(suf)] in listed:
            return token[: -len(suf)]
    head = token.split("-")[0]
    return head if head in listed else token


def main():
    text = open("main.md", encoding="utf-8").read()
    lst = section(text, "Abbreviations")
    if lst is None:
        print("INFO  main.md has no '# Abbreviations' section; nothing checked")
        return
    listed = {}
    for line in lst.split("\n"):
        m = re.match(r"^- (.+?):\s*(.+)$", line)
        if m:
            for abbr in re.findall(r"\*\*([^*]+)\*\*", m.group(1)):
                listed[abbr] = m.group(2)

    body = text[text.index("# Abstract"): text.index("# References")]
    body = re.sub(r"https?://\S+", "", body)
    body = re.sub(r"^\*\[.*\]\*$", "", body, flags=re.M)  # template placeholders
    body = body.replace(lst, "")
    prose = re.sub(r"```.*?```", "", body, flags=re.S)
    hl = section(prose, "Highlights")
    if hl:
        prose = prose.replace(hl, "")
    prose = "\n".join(l for l in prose.split("\n") if not l.lstrip().startswith("|") and not l.startswith("#"))

    notes, used = [], set()
    for tok in TOKEN.findall(body):
        if sum(ch.isupper() for ch in tok) < 2 and not re.match(r"\d[A-Z]", tok):
            continue
        if tok in IGNORE:
            continue
        key = fold(tok, listed)
        if key in listed:
            used.add(key)
        elif key not in IGNORE:
            notes.append(("WARN", f"'{tok}' is not in the Abbreviations list (add it, or add it to IGNORE if it is a name)"))
    for abbr in listed:
        m = re.search(r"(?<![A-Za-z0-9])" + re.escape(abbr) + r"(?![A-Za-z0-9])", prose)
        if not m:
            if abbr not in used:
                notes.append(("INFO", f"'{abbr}' is listed but not used"))
            continue
        # "(hiPSC-CMs)" also defines "hiPSC", so a hyphen may follow the abbreviation
        defined = r"\((?:[^()]*\s)?" + re.escape(abbr) + r"s?[-),;]|" + re.escape(abbr) + r" (?:=|is)\s"
        end = prose.find(". ", m.end())
        if not re.search(defined, prose[: end + 1 if end > 0 else len(prose)]):
            line = prose[: m.start()].count("\n") + 1
            context = prose[max(0, m.start() - 40): m.end() + 20].replace("\n", " ")
            notes.append(("WARN", f"'{abbr}' first used without being spelled out: ...{context}..."))
    seen = set()
    for level, msg in notes:
        if msg not in seen:
            seen.add(msg)
            print(f"{level:5} {msg}")
    print(f"{len(listed)} listed, {len(used)} used, {sum(1 for l, m in notes if l == 'WARN' and m in seen)} warning(s)")


main()
