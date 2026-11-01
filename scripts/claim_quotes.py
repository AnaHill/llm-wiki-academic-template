"""Attach the sentences of main.md that cite a source under that source's claims in docs/claims-by-source.md.

The claims file has one section per source, headed as the source is cited in main.md, e.g.
`## Smith et al. (2023)`, `## Smith & Jones (2023)` or `## Smith (2023)` (more text may follow the year).
Under it, every numbered claim line such as `- [ ] (2) [Related Work] ...` carries a tag in brackets: the start of
the main.md heading the claim sits in (case-insensitive; `[Intro]` matches "Introduction"; several tags may be
separated by commas). For each claim, the sentences of main.md under a matching heading that cite the same source
(first author's surname and year) are listed below the claim as `    - > sentence — main.md:line` sub-bullets.
Only those generated sub-bullets are rewritten; checkbox state, claim text and everything else in the file are kept.
Sections without a year in the heading (e.g. the register of the author's own inferences) are left alone.

Usage (run from the repository root):
    python -I scripts/claim_quotes.py                       dry run for all sources: prints the result, writes nothing
    python -I scripts/claim_quotes.py --only Smith          dry run for the sources whose heading starts so
    python -I scripts/claim_quotes.py --write --skip Smith  update the file for all sources except those named
Options may be repeated. A sentence is assigned to a claim only by the section tag, so two claims with the same tag
show the same sentences; the generated quotes are a pointer to the text, not a judgement of which claim they support.
A sentence that continues a citation without naming the source ("The same study ...") is not found.
"""
import argparse
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

MAIN = "main.md"
CLAIMS = "docs/claims-by-source.md"

ABBREVIATIONS = {"al", "e.g", "i.e", "vs", "fig", "figs", "approx", "cf", "ca", "no", "dr", "eg", "ie"}

CLAIM = re.compile(r"^- \[[ xX]\] \((\d+[a-z]?)\) \[([^\]]+)\]")
GENERATED = re.compile(r"^ {4}- > ")
SOURCE_HEADING = re.compile(r"^## ([^\s(,&]+(?:[ -][^\s(,&]+)?)(?: et al\.| (?:&|and) [^\s(]+)?,? \((\d{4})")


def split_sentences(text):
    """Split a paragraph into sentences; keeps 'et al.' and initials together."""
    out, start = [], 0
    for m in re.finditer(r"[.!?][)*\"”]*\s+(?=[A-Z*\[“\"(])", text):
        end = m.start() + len(m.group(0).rstrip())
        token = re.search(r"(\S+)$", text[:m.start() + 1]).group(1).rstrip(".!?").lstrip("(*")
        if token.lower() in ABBREVIATIONS or re.fullmatch(r"[A-Z]", token):
            continue
        out.append(text[start:end])
        start = m.end()
    out.append(text[start:])
    return [s.strip() for s in out if s.strip()]


def main_sentences():
    """Return [(heading title, line number, sentence)] for the body of main.md (everything before # References)."""
    lines = open(MAIN, encoding="utf-8").read().split("\n")
    result, current, fence, front = [], None, False, False
    for number, raw in enumerate(lines, 1):
        if number == 1 and raw.strip() == "---":
            front = True
            continue
        if front:
            front = raw.strip() != "---"
            continue
        if re.match(r"^# References\s*$", raw):
            break
        line = re.sub(r"<!--.*?-->", "", raw).rstrip()
        if raw.strip().startswith("```"):
            fence = not fence
            continue
        heading = re.match(r"^(#{1,3}) (.+)", line)
        if heading and not fence:
            current = heading.group(2).strip()
            continue
        if current is None or not line.strip():
            continue
        if line.lstrip().startswith("|") or fence:
            # Mermaid labels use a literal \n for line breaks; it would hide a name that follows it from \b
            text = line.strip().replace("\\n", " ") if fence else line.strip()
            result.append((current, number, re.sub(r"\s{2,}", " ", text)))
        else:
            for sentence in split_sentences(line.strip()):
                result.append((current, number, sentence))
    return result


def tag_matches(tag, title):
    return title.lower().startswith(tag.lower())


def source_pattern(heading):
    """'## Smith et al. (2023) ...' -> (name, regex for 'Smith ... 2023' within one citation)."""
    m = SOURCE_HEADING.match(heading)
    if not m:
        return None
    surname, year = m.group(1), m.group(2)
    name = heading[3:].strip()
    return name, re.compile(rf"\b{re.escape(surname)}\b[^()\n]{{0,40}}?\(?{year}")


def quote_lines(sentences, pattern, tag):
    seen, lines = set(), []
    for title, number, sentence in sentences:
        if tag_matches(tag, title) and pattern.search(sentence) and (number, sentence) not in seen:
            seen.add((number, sentence))
            lines.append(f"    - > {sentence} — main.md:{number}")
    return lines


def update(claim_lines, sentences, selected):
    out, source, notes, shown, tags_by_source = [], None, [], [], {}
    i, in_comment = 0, False
    while i < len(claim_lines):
        line = claim_lines[i]
        if in_comment or line.lstrip().startswith("<!--"):
            in_comment = "-->" not in line
            out.append(line)
            i += 1
            continue
        if line.startswith("## "):
            source = source_pattern(line)
            if source and selected(source[0]):
                shown.append(line)
                tags_by_source.setdefault(source, set())
        m = CLAIM.match(line)
        if m and source and selected(source[0]):
            out.append(line)
            shown.append(line)
            i += 1
            while i < len(claim_lines) and GENERATED.match(claim_lines[i]):
                i += 1
            for tag in [t.strip() for t in m.group(2).split(",")]:
                tags_by_source[source].add(tag)
                found = quote_lines(sentences, source[1], tag)
                if not found:
                    notes.append(f"{source[0]} claim ({m.group(1)}) [{tag}]: no sentence found in main.md")
                out.extend(found)
                shown.extend(found)
            continue
        out.append(line)
        i += 1
    for (name, pattern), tags in tags_by_source.items():
        cited = {title for title, _, s in sentences if pattern.search(s)}
        for title in sorted(cited):
            if not any(tag_matches(tag, title) for tag in tags):
                notes.append(f"{name}: cited in main.md section '{title}' but no claim carries a matching tag")
    return out, notes, shown


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write", action="store_true", help="update docs/claims-by-source.md (default: dry run)")
    parser.add_argument("--only", action="append", default=[], help="only sources whose heading starts with this")
    parser.add_argument("--skip", action="append", default=[], help="leave sources whose heading starts with this")
    args = parser.parse_args()

    def selected(name):
        if args.only and not any(name.startswith(o) for o in args.only):
            return False
        return not any(name.startswith(s) for s in args.skip)

    original = open(CLAIMS, encoding="utf-8").read().split("\n")
    updated, notes, shown = update(original, main_sentences(), selected)
    if args.write:
        open(CLAIMS, "w", encoding="utf-8", newline="\n").write("\n".join(updated))
        print(f"wrote {CLAIMS}")
    else:
        print("dry run: nothing written\n")
        print("\n".join(shown))
    if notes:
        print("\nNotes:")
        for note in notes:
            print("-", note)


main()
