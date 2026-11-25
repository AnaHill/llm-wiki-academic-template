---
name: ingest
description: Turn a source document in raw/ into wiki pages - a paper page, concept-page updates, the reference entry, the index line and a log entry - and rename the raw file to match. Also the verify-first pass when the researcher says new files were added without naming them. Use when asked to ingest, process or add a paper or PDF, or to check what is new in raw/.
license: MIT
---

# Ingest

The rules of AGENTS.md apply throughout, above all: never invent bibliographic details, and never change the text of a file in `raw/`.

## New files without names: verify first

If the researcher says something like "I added sources to raw/, go check them" without naming files, find the new ones (`git status` for untracked files in `raw/`, or `raw/` against the paper list in `wiki/index.md`). Read each and report a verdict per source — worth ingesting, marginal, or out of scope — and stop. Create no pages, rename nothing and touch neither `wiki/references.md` nor `main.md` until the researcher names the sources to ingest.

## Steps for one source

1. **Read the source in full.** If the Read tool cannot open a PDF, run `python -I scripts/render_pdf_pages.py raw/<file>.pdf --text` and read `figure_analysis/<pdf-name>/text.txt`. For figures, run it again without `--text` (it finds pages with figure or table captions; `--pages 3,5` limits it) and view the PNGs. Describe what each figure shows; say when a schematic carries no data.
2. **Read the supplementary files too:** they hold the per-sample data and the conditions that the main text summarises, and they can change a claim. For a `.docx` supplement, the images are in the zip archive under `word/media/`; extract them to `figure_analysis/<stem>/` to view them.
3. **Take the bibliographic details from the source itself:** the author order from page 1 of the PDF, the venue, the DOI, and both the online-first and the issue dates. Note any place where the source disagrees with itself (text versus figure caption, abstract versus results).
4. **Discuss the key takeaways** if the researcher wants to stay involved.
5. **Create the paper page** `wiki/papers/<firstauthor-year-keyword>.md` in the format below, and in the same step **rename the raw file** to the same stem (below). Check the page against the source text before moving on: an error made at ingest is copied into concept pages, the index, the draft and the claim register, and gets harder to remove at every step.
6. **Update concept, method and research-gap pages** the source bears on. Link the concept pages that cite the paper from its "See also", and give a short reason after a link to another paper ("— definition A versus definition B"). Two to four tags from the Tag vocabulary.
7. **Append the reference** to `wiki/references.md` (References rule of AGENTS.md: APA, issue year, both dates on the paper page; do not convert existing entries to another style).
8. **Add the index line** to `wiki/index.md`, under the categories defined there: link, one-line summary, optionally year and venue.
9. **Append the log entry** `## [YYYY-MM-DD] ingest | Author Year — Paper Title`, naming the pages touched, with a line that records what steps 1–3 actually did (`check.py` warns when it is missing from an ingest entry):
   `Checks: full text read (or why not) | figures viewed: pages 3, 5 (or none with data) | supplements: read (or none) | authors from page 1 | dates: online-first …, issue … | inconsistencies: none (or where they are recorded)`
10. **Run `python -I scripts/check.py`** and fix its ERRORs. If the source shares a first-author surname with another source, tell the researcher: the in-text citation rule for that case has to be decided (see "Citations and the reference list" in the `draft` skill), and if the year is the same too, `claim_quotes.py` (which matches a source by surname and year) gives both sources the same sentences until their claims are narrowed with `{q: ...}`.
11. **Mention `/grinding wiki <source>` once**, at the end of the batch rather than after every source: the check of the new pages and the wiki sentences citing them against the sources, before anything from them reaches `main.md`. Running it, and when, is the researcher's choice; several sources are often added before the wiki is checked.

A single source often touches 5–10 wiki pages. **Done when:** the page, the renamed raw file, the reference, the index line and the log entry with its `Checks:` line exist, and `check.py` reports no ERROR for the source.

## Naming the raw file

The raw file and its page share one stem: `raw/XYZ.pdf` that becomes `wiki/papers/smith-2025-keyword.md` is renamed to `raw/smith-2025-keyword.pdf` (extension unchanged), and supplements to `raw/smith-2025-keyword-supplementary.<ext>` whatever their format (`.pdf`, `.docx`, `.xlsx`), linked from the page with a `**Supplementary:** [[raw/...]]` line. Do the rename in the same step as creating the page, so its `**File:** [[raw/...]]` line is right from the start. Only the name changes, never the content. Use `git mv` for a tracked file, a plain move otherwise. Rename only files the researcher has asked you to ingest, never during the verify-first pass. Check `.gitignore` for the old name first (non-open-access PDFs should be git-ignored by name); if it is listed, tell the researcher the entry must change to the new name, so the PDF does not become trackable by accident.

## Paper page format

```markdown
---
tags: [theme-tag, theme-tag]
---

# Title

**Authors:** …  
**Year:** …  
**Venue:** …  
**File:** [[raw/filename.pdf]]  
**Supplementary:** [[raw/filename-supplementary.ext]]  (when there is one)  
**DOI:** …

## Contribution
One paragraph: what does this paper claim to contribute?

## Methodology
Key methods, datasets, experimental setup.

## Findings
Main results and conclusions.

## Limitations
What the authors acknowledge as limitations or what you observe.

## Relevance to our paper
How this source relates to, supports, challenges, or fits into the paper being written.

## See also
Links to related wiki pages.
```
