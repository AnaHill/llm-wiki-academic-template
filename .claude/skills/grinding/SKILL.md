---
name: grinding
description: Check what is written about one source against the source itself and report a verdict per claim (holds / check / does not hold) with quotes and pages. Two targets - the claims of main.md listed in docs/claims-by-source.md (default), or with "wiki" the source's paper page and every wiki sentence citing it, right after ingest. Read-only until the researcher asks for fixes.
argument-hint: [wiki] <source, e.g. Smith or "Lee 2026">
disable-model-invocation: true
license: MIT
---

# Grinding

The researcher's word for the claim-by-claim check of what is written against its sources. Read AGENTS.md first; its rules (never invent citations or findings, `notes.md` is read-only, surgical changes) apply throughout.

The argument names one source, for example `Smith`, `Lee 2026` or `Park 2025`. With `wiki` before it (`/grinding wiki Smith`), follow "Wiki mode" below instead of the Steps; the source is read and checked the same way, only the claims come from the wiki.

## Steps

1. **Find the section.** Match the argument to a `## <Author> et al. (<year>)` heading in `docs/claims-by-source.md` (a ✅ in front of the heading only means all boxes are ticked). If several headings match (for example Lee 2024 and Lee 2026) or none does, ask which one and stop.
2. **Read the section:** the "Local file" and status line, every claim `(n)` with its `- >` lines (the sentences of `main.md` as of the last `claim_quotes.py --write`, without line numbers) and the Pointers line. Check each quoted sentence against `main.md` itself; if the `- >` lines are stale, say so and use the current text. To locate a sentence, search for its text, or run `python -I scripts/claim_quotes.py --only <source>`, whose dry run prints the line number beside every quote.
3. **Read the source in full,** not only the pages named in Pointers. Use the Read tool on the PDF; if that fails (for example `pdftoppm` missing), run `python -I scripts/render_pdf_pages.py raw/<file>.pdf --text` and read `figure_analysis/<name>/text.txt`. Read supplementary files in `raw/` when a claim depends on them. For a claim that rests on a figure, render and view that page.
4. **Check each claim** against the passage that supports or contradicts it, with its page (and figure or table). Look in particular for:
   - wording stronger than the source ("shown" where the source says "largely", "suggest", "may be linked", "appears");
   - numbers, units, ranges, cell types, species and conditions that differ from the source;
   - a condition or limitation of the source that the sentence in `main.md` drops;
   - parts of the sentence that are the author's own inference: name the register item in `docs/claims-by-source.md` that covers it, or say that none does;
   - the source disagreeing with itself (text versus figure caption): report both values;
   - errors in the wiki page or the Pointers line, even when `main.md` is not affected.
5. **Change nothing.** Report as below and wait.

## Report

Write in the language the researcher used; keep quotations in the original language. Use this shape:

1. One opening line: how the source was read (Read tool or text dump, figures or supplement if used), that no files were changed, and the overall verdict ("all six hold, two have a minor note").
2. A summary table:

   | # | Where in main.md | Verdict |
   |---|---|---|
   | 1 | Related Work, line 110 | ✅ holds |

   Verdicts: ✅ holds, ✅ holds (with a short note), ⚠️ check (wording, a missing condition or a number), ❌ does not hold.
3. One section per claim, separated by `---`:

   ```
   ### (n) <short title>: <verdict>
   **main.md:<line>:** "<quoted sentence or the relevant part>"
   **Source:** "<quoted passage>" (p. X; Fig./Table if relevant)

   **Note:** <only if needed>
   **Suggestion:** <concrete new wording, only for ⚠️ or ❌>
   ```

   Translate the bold labels into the researcher's language.
4. A closing summary: what should be fixed, what is optional, and whether the claims are ready to be ticked. Offer the fixes; do not apply them.

Never tick a box yourself; ticking is the researcher's decision.

## When the researcher asks for fixes

Apply only the fixes named. Then, following the `draft` skill (`.claude/skills/draft/SKILL.md`):

- edit `main.md` surgically, and keep the matching claim in `docs/claims-by-source.md` in step (reword it, note the change and its date; when a claim is dropped or merged, renumber and update every reference to its number, such as the register);
- fix the wiki page and the Pointers line when they were wrong;
- add or update a register item for any new own inference;
- after a change of wording, re-read the title, the Highlights (register item 0) and the Abstract: a summary that restates the changed claim does not change with it, and only a quoted wording in the register is checked by script;
- append a `wiki/log.md` entry (`draft` when `main.md` changed, otherwise `query`);
- run `python -I scripts/claim_quotes.py --write`, `python -I scripts/check.py` and, if `main.md` changed, `python -I scripts/check_abbreviations.py`;
- end with a proposed commit message in the style the researcher uses.

## Wiki mode

The check at the wiki layer, before a claim reaches `main.md`: an error caught on the paper page is not yet copied to the concept pages, the claims file and the paper.

1. **Find the page.** Match the argument to a page in `wiki/papers/`; if several match or none does, ask and stop.
2. **Collect the claims:** every statement of the paper page about the source (the bibliographic lines, Contribution, Methodology, Findings, Limitations; "Relevance to our paper" only where it states a fact about the source), and every sentence on other wiki pages (concept pages, `wiki/index.md`) that links to the page or cites the source. Number them in that order.
3. **Read the source in full** and **check each claim** as in steps 3–4 above, the bibliographic lines included: the author order against page 1, the venue, the DOI, and both dates.
4. **Change nothing.** Report as above, with "Where in the wiki" (page and line) in place of "Where in main.md", and say which sentences of `main.md` repeat a claim that does not hold, so they can be checked next with `/grinding <source>`.

When the researcher asks for fixes, apply only those named, fix the same claim on every wiki page that repeats it, append a `## [YYYY-MM-DD] lint | wiki grinding <source>` log entry and run `python -I scripts/check.py`. When the researcher says the page is checked (their decision, as with ticking), add or update the line `**Checked against source:** YYYY-MM-DD` after the **DOI:** line of the paper page. `check.py` lists the pages without that line, and a page changed in a later commit than its date.

## When not to use it

Deciding whether a claim should stay in the paper at all, or how strongly to state it: use `/grill-paper`. Register items of the author's own inferences have no source to check against; there the researcher decides whether they stand behind the wording.
