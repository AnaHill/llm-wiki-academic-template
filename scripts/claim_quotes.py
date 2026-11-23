"""Attach the sentences of main.md that cite a source under that source's claims in docs/claims-by-source.md.

The claims file has one section per source, headed as the source is cited in main.md, e.g.
`## Smith et al. (2023)`, `## Smith & Jones (2023)` or `## Smith (2023)` (more text may follow the year).
Under it, every numbered claim line such as `- [ ] (2) [Related Work] ...` carries a tag in brackets: the start of
the main.md heading the claim sits in (case-insensitive; `[Intro]` matches "Introduction"; several tags may be
separated by commas). For each claim, the sentences of main.md under a matching heading that cite the same source
(first author's surname and year) are listed below the claim as `    - > sentence` sub-bullets.
Only those generated sub-bullets are rewritten; checkbox state, claim text and everything else in the file are kept.
Sections without a year in the heading (e.g. the register of the author's own inferences) get no quotes.

The stored lines carry no main.md line number, deliberately: a number changes in every quote below an edit whenever
a paragraph is split or a heading added, which buries the quotes that really changed. Without it a quote line
changes only when its sentence does, so `git diff docs/claims-by-source.md` shows exactly which claims moved. The
dry run prints the numbers, which is where they are useful.

Usage (run from the repository root):
    python -I scripts/claim_quotes.py                       dry run: prints the result with main.md line numbers,
                                                            writes nothing
    python -I scripts/claim_quotes.py --only Smith          dry run for the sources whose heading starts so
    python -I scripts/claim_quotes.py --write               update the file and refresh the ✅ marks
    python -I scripts/claim_quotes.py --write --skip Smith  update the file for all sources except those named
    python -I scripts/claim_quotes.py --check               only say whether the file is out of date, and the Notes
                                                            (what the main.md hook runs)
Options may be repeated. A sentence is assigned to a claim by the section tag, so two claims with the same tag show
the same sentences unless the claim narrows them itself: a claim line may end with `{q: <regex>}`, and then the
sentences of that section matching that regex are listed under it instead. Use it where one section holds several
claims about the same source. The regex replaces the citation test, so it also reaches a sentence that continues a
citation without naming the source ("The same study ..."), which is otherwise not found at all. A regex that matches
nothing is reported, and so is a sentence citing the source that no claim lists once any claim of that section is
narrowed.

With --write, a `## ` section whose top-level checkboxes are all ticked gets a "✅ " in front of its title, and loses
it again when a box is unticked.

The register of the author's own inferences (the `## ` section of that name) quotes main.md by hand in its
**Text:** lines; a quoted wording that main.md no longer contains is reported, because a summary that outlives the
sentence it summarises is an error no other check sees. Old wordings kept in parentheses are skipped as history.

Both failure modes of this script produce nothing rather than an error: a claim whose tag no longer matches a
heading (after a section was renamed) and a source whose citations no longer match its heading collect no quotes.
Read the Notes after every run, and run without --write first after a structural edit to main.md.
"""
import argparse
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

MAIN = "main.md"
CLAIMS = "docs/claims-by-source.md"
REGISTER = "Register of the author's own inferences"  # the one `## ` section that is not a source
DONE = "✅ "

ABBREVIATIONS = {"al", "e.g", "i.e", "vs", "fig", "figs", "approx", "cf", "ca", "no", "dr", "eg", "ie"}

CLAIM = re.compile(r"^- \[[ xX]\] \((\d+[a-z]?)\) \[([^\]]+)\]")
NARROW = re.compile(r"\{q:\s*(.+?)\}\s*$")
GENERATED = re.compile(r"^ {4}- > ")
CHECKBOX = re.compile(r"^- \[([ xX])\] ")
SOURCE_HEADING = re.compile(r"^([^\s(,&]+(?:[ -][^\s(,&]+)?)(?: et al\.| (?:&|and) [^\s(]+)?,? \((\d{4})")


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
    """Return ([(heading title, line number, sentence)], [heading titles]) for main.md before # References."""
    lines = open(MAIN, encoding="utf-8").read().split("\n")
    result, headings, current, fence, front = [], [], None, False, False
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
            headings.append(current)
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
    return result, headings


def tag_matches(tag, title):
    return title.lower().startswith(tag.lower())


def source_pattern(heading):
    """'## Smith et al. (2023) ...' -> (name, regex for 'Smith ... 2023' within one citation)."""
    title = heading[3:].removeprefix(DONE).strip()
    m = SOURCE_HEADING.match(title)
    if not m:
        return None
    surname, year = m.group(1), m.group(2)
    return title, re.compile(rf"\b{re.escape(surname)}\b[^()\n]{{0,40}}?\(?{year}")


def quote_lines(sentences, pattern, tag):
    """[(stored line, main.md line number, heading title)] for the sentences under headings matching `tag`
    that match `pattern`."""
    seen, lines = set(), []
    for title, number, sentence in sentences:
        if tag_matches(tag, title) and pattern.search(sentence) and (number, sentence) not in seen:
            seen.add((number, sentence))
            lines.append((f"    - > {sentence}", number, title))
    return lines


def update(claim_lines, sentences, headings, selected):
    out, source, notes, shown, tags_by_source = [], None, [], [], {}
    narrowed, listed = set(), {}  # (source, heading) pairs reached by a {q: ...} claim, and the quote lines listed
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
            narrowing = NARROW.search(line)
            narrow = None
            if narrowing:
                try:
                    narrow = re.compile(narrowing.group(1))
                except re.error as error:
                    notes.append(f"{source[0]} claim ({m.group(1)}): {{q: {narrowing.group(1)}}} is not a valid regex ({error})")
            for tag in [t.strip() for t in m.group(2).split(",")]:
                tags_by_source[source].add(tag)
                if not any(tag_matches(tag, h) for h in headings):
                    notes.append(f"{source[0]} claim ({m.group(1)}) [{tag}]: no heading of main.md starts with "
                                 f"'{tag}' — was the section renamed? Update the tag")
                    continue
                found = quote_lines(sentences, narrow or source[1], tag)
                if not found:
                    reason = f" matching {{q: {narrowing.group(1)}}}" if narrow else ""
                    notes.append(f"{source[0]} claim ({m.group(1)}) [{tag}]: no sentence found in main.md{reason}")
                for text, _, title in found:
                    listed.setdefault((source, title), set()).add(text)
                if narrow:
                    narrowed.update((source, h) for h in headings if tag_matches(tag, h))
                out.extend(text for text, _, _ in found)
                shown.extend(f"{text} — main.md:{number}" for text, number, _ in found)
            continue
        out.append(line)
        i += 1
    for (name, pattern), tags in tags_by_source.items():
        cited = {title for title, _, s in sentences if pattern.search(s)}
        for title in sorted(cited):
            if not any(tag_matches(tag, title) for tag in tags):
                notes.append(f"{name}: cited in main.md section '{title}' but no claim carries a matching tag")
    # Where {q: ...} is used, every sentence of that section citing the source should still be under some claim.
    for source, heading in sorted(narrowed, key=lambda pair: (pair[0][0], pair[1])):
        for title, number, sentence in sentences:
            if title == heading and source[1].search(sentence)                     and f"    - > {sentence}" not in listed.get((source, heading), set()):
                notes.append(f"{source[0]} '{heading}': no claim lists main.md:{number} {sentence[:90]}…")
    return out, notes, shown


def _top_level_quotes(text):
    """The "double-quoted" strings of `text` that are not inside parentheses (parentheses keep old wordings)."""
    out, depth, i = [], 0, 0
    while i < len(text):
        c = text[i]
        if c == '"':
            j = text.find('"', i + 1)
            if j < 0:
                break
            if depth == 0 and not text[j + 1:].lstrip().startswith("became"):
                out.append(text[i + 1:j])  # '"old" became "new"': the first one is history too
            i = j + 1
            continue
        depth += {"(": 1, ")": -1}.get(c, 0)
        depth = max(depth, 0)
        i += 1
    return out


def _flat(text):
    text = text.replace("*", "").replace("\\#", "#").replace("’", "'")
    return re.sub(r"\s+", " ", text).strip().lower()


def register_drift(claim_lines):
    """Notes for quoted wordings in the register (**Text:** lines) that main.md no longer contains.

    Each quote is split at an ellipsis and every fragment of 12 or more characters must occur in main.md,
    ignoring case, emphasis markers and line breaks.
    """
    main_text = _flat(open(MAIN, encoding="utf-8").read())
    notes, item, inside, in_comment = [], None, False, False
    for line in claim_lines:
        if in_comment or line.lstrip().startswith("<!--"):  # the template's example item lives in a comment
            in_comment = "-->" not in line
            continue
        if line.startswith("## "):
            inside = line[3:].removeprefix(DONE).strip() == REGISTER
            continue
        if not inside:
            continue
        m = re.match(r"- \[[ xX]\] \*\*(\d+)\.", line)
        if m:
            item = m.group(1)
            continue
        m = re.match(r"\s+- \*\*(?:Text:|\(\d+\))\*\*\s*(.*)", line)
        if not m or item is None:
            continue
        for quote in _top_level_quotes(m.group(1)):
            for fragment in re.split(r"\s*(?:…|\.\.\.)\s*", quote):
                fragment = _flat(fragment).strip(" ,;:")
                if len(fragment) >= 12 and fragment not in main_text:
                    notes.append(f'register item {item}: quoted wording not found in main.md: "{fragment[:90]}" — '
                                 f'update the quote, or put the old wording in parentheses as history')
    return notes


def mark_done(lines):
    """Put DONE in front of every `## ` title whose top-level checkboxes are all ticked; remove it otherwise.

    Lines inside HTML comments (such as the example section of the template) are left alone.
    """
    out, changed, live, in_comment = list(lines), [], [], False
    for line in lines:
        commented = in_comment or line.lstrip().startswith("<!--")
        live.append(not commented)
        if commented:
            in_comment = "-->" not in line
    starts = [i for i, line in enumerate(lines) if line.startswith("## ") and live[i]] + [len(lines)]
    for start, end in zip(starts, starts[1:]):
        boxes = [CHECKBOX.match(line).group(1) for k, line in enumerate(lines[start + 1:end], start + 1)
                 if live[k] and CHECKBOX.match(line)]
        title = lines[start][3:].removeprefix(DONE)
        heading = "## " + (DONE if boxes and all(b in "xX" for b in boxes) else "") + title
        if heading != lines[start]:
            out[start] = heading
            changed.append(heading)
    return out, changed


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write", action="store_true", help="update docs/claims-by-source.md (default: dry run)")
    parser.add_argument("--only", action="append", default=[], help="only sources whose heading starts with this")
    parser.add_argument("--skip", action="append", default=[], help="leave sources whose heading starts with this")
    parser.add_argument("--check", action="store_true",
                        help="print only whether the file is out of date and the Notes (used by the main.md hook)")
    args = parser.parse_args()

    def selected(name):
        if args.only and not any(name.startswith(o) for o in args.only):
            return False
        return not any(name.startswith(s) for s in args.skip)

    original = open(CLAIMS, encoding="utf-8").read().split("\n")
    sentences, headings = main_sentences()
    updated, notes, shown = update(original, sentences, headings, selected)
    notes += register_drift(original)
    updated, changed = mark_done(updated)
    if args.check:
        stale = sum(1 for a, b in zip(original, updated) if a != b) + abs(len(original) - len(updated))
        if stale:
            print(f"{CLAIMS} is out of date with main.md ({stale} line(s) would change); "
                  "run python -I scripts/claim_quotes.py --write")
        else:
            print(f"{CLAIMS} is up to date with main.md")
        if notes:
            print("Notes:")
            for note in notes:
                print("-", note)
        return
    if args.write:
        open(CLAIMS, "w", encoding="utf-8", newline="\n").write("\n".join(updated))
        print(f"wrote {CLAIMS}")
        for heading in changed:
            print("heading updated:", heading)
    else:
        print("dry run: nothing written\n")
        print("\n".join(shown))
        for heading in changed:
            print("heading would change to:", heading)
    if notes:
        print("\nNotes:")
        for note in notes:
            print("-", note)


main()
