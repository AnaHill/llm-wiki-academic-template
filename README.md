# LLM Academic Wiki

A wiki template for academic researchers, maintained by an AI agent, using VS Code as the editor. The pattern works with any LLM agent that reads an instruction file: the instructions are in `AGENTS.md` (read by Codex, Cursor and others), and `CLAUDE.md` imports it for [Claude Code](https://claude.ai/code).

Drop a paper (PDF/other) into `raw/`. The LLM reads it, writes a summary page, updates the concept and gap pages, and appends a citation to the reference list. When you're ready to write, tell it to draft or update a section of `main.md` — it draws from everything it has read. Helper scripts check that citations, the reference list and the wiki stay consistent.

Based on [Andrej Karpathy's LLM wiki idea](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). For a complete paper written with this template, including the lessons that shaped its scripts and conventions, see [MEA_review_llm_wiki](https://github.com/AnaHill/MEA_review_llm_wiki).

---

## Quick start

### Starting a new paper project (recommended)

Use the GitHub template to get a clean repo with no connection to this template:

```bash
gh repo create my-paper-on-topic-X --public --template AnaHill/llm-wiki-academic-template --clone
cd my-paper-on-topic-X
```

Or click **"Use this template"** on [github.com/AnaHill/llm-wiki-academic-template](https://github.com/AnaHill/llm-wiki-academic-template) and clone the result.

Each paper gets its own isolated repo. Edit `AGENTS.md` to tailor the wiki schema for that paper's topic.

### Then

1. Open the project folder in VS Code and start an AI agent session in this directory.
2. Drop a paper (PDF/other) into `raw/` and say: **"ingest `raw/<filename>`"**
3. When ready to write: open `main.md`, select a section, and say e.g. **"write the introduction"**.
4. After changes, the agent runs `python -I scripts/check.py`; you can run it yourself at any time.

Requirements for the scripts: Python 3; `render_pdf_pages.py` also needs [PyMuPDF](https://pymupdf.readthedocs.io/) (`pip install pymupdf`), and `figures.py --render` needs Edge or Chrome. The other scripts use the standard library only.

---

## How it works

| Layer | Path | Who owns it |
|-------|------|-------------|
| Source papers | `raw/` | You — PDFs, notes. Immutable (files are only renamed at ingest). |
| Wiki pages | `wiki/` | LLM — paper summaries, concepts, gaps |
| Paper draft | `main.md` | LLM writes, you direct and edit |
| Own thinking | `notes.md` | You only; the agent reads it, never edits it |
| Process records | `docs/` | Claim register, lessons, literature search records, export notes |

```
ingest PDF                                    write draft
    │                                              │
    ▼                                              ▼
raw/ ──► wiki/papers/ ──► wiki/index.md ──► main.md ──► docs/claims-by-source.md
              │                   │                        (verify each claim
              └── wiki/references.md (citations)            against its source)
```

**Operations:**
- **Ingest** — LLM reads a PDF, creates a paper page, updates concepts/gaps, appends citation
- **Query** — ask anything; LLM reads the wiki and synthesizes an answer with citations
- **Draft** — ask to write or rewrite any section of `main.md`
- **Lint** — health check: stale claims, orphans, unsupported draft assertions; runs `scripts/check.py`
- **Literature search** — the agent records queries, dates and counts in `docs/`, so the paper can describe the search truthfully

Before a non-trivial choice (what a section should claim, which sources to ingest or cite, which lint findings to fix), type `/grill-paper` (Claude Code): the agent interviews you in rounds, looks up the facts in the wiki itself and leaves the decisions to you.

To check the claims cited to one source, type `/grinding <source>` (for example `/grinding Smith`): the agent reads the source in full and reports a verdict per claim in `docs/claims-by-source.md`, with the sentence from `main.md`, the supporting passage and its page, without changing anything. `/grinding wiki <source>` does the same one layer earlier, right after ingest: it checks the source's wiki page and every wiki sentence that cites it, so an error is caught before it is copied into concept pages and the paper; a page the author accepts gets a `**Checked against source:**` date, and `check.py` lists the pages without one.

[AGENTS.md](AGENTS.md) holds only what applies to every task (layout, hard rules, the Tag vocabulary, references, logging, the finishing check); the procedures are skills in [.claude/skills/](.claude/skills/): `ingest`, `draft` and `lint`, which Claude Code loads by their description when a task matches, and `grill-paper` and `grinding`, which run only when called. Other agents (Codex and the like) read AGENTS.md, whose table names the skill file to read for each task, so the template does not depend on Claude Code. See [llm-wiki.md](llm-wiki.md) for the concept.

---

## Checking the paper against its sources

An LLM-maintained wiki can copy one misreading from a summary page into the index, the draft and the abstract. Three tools catch different kinds of error:

- `scripts/check.py` — structural errors: a citation without a reference entry, a paper page without a raw file or with a first author that differs from its reference key, DOIs that differ, broken links, a `# References` list in `main.md` that is not a verbatim copy of `wiki/references.md`, accidental Obsidian tags, sources compared in `main.md` whose wiki pages are not connected, a rendered figure older than its diagram. It cannot tell whether a claim is true.
- `docs/claims-by-source.md` — a checklist of every claim `main.md` attributes to each source, which you tick off against the source itself (`/grinding` reads the source and proposes a verdict per claim). Its last section registers the author's own inferences, each with a **Support** value saying where its warrant comes from. `scripts/claim_quotes.py` lists under each claim the sentences of `main.md` that cite the source, without line numbers, so `git diff` shows exactly which claims moved; it also reports a quoted wording in the register that `main.md` no longer contains.
- Your own reading of the whole draft — contradictions between sections, partial fixes that left a sentence contradicting itself, and a title, highlight or abstract line that still says what the body has withdrawn.

## The harness around the agent

Most of the work is not prompting but the setup around the agent. Each piece of it in this template was added in the project it comes from because something went wrong without it; [docs/lessons.md there](https://github.com/AnaHill/MEA_review_llm_wiki/blob/master/docs/lessons.md) says what.

- **Instructions:** `AGENTS.md`, one file with one owner, kept short because it goes with every request.
- **Thin tools:** small scripts in `scripts/`, each doing one mechanical job and returning plain text the agent can read, plus `eval_skills.py`, which checks with headless Claude Code runs that each task still loads its skill.
- **Skills that load on demand (progressive disclosure):** the procedures needed only for some tasks live in `.claude/skills/`: `ingest`, `draft` (with the details of the claims file in a reference file of its own, read only when the claims file is edited) and `lint`, and `/grill-paper` and `/grinding`.
- **Guardrails in the harness, not only in the prompt:** `.claude/settings.json` denies edits to `notes.md` and asks before any write to `raw/` and keeps the agent from reading the Obsidian folder and the export files, which only duplicate `main.md` in its context, and hooks (`scripts/hooks/harness.py`) run the abbreviation, consistency and claims checks after every edit of `main.md`; report a shell command that changed `notes.md` or a file in `raw/`, which the permission rules do not cover; and, when the agent is about to finish with uncommitted changes in the wiki or the paper, run the finishing check and keep it working on an error.
- **Rule plus mechanical check:** a rule in `AGENTS.md` alone gets forgotten, and a script alone cannot judge, so each important convention has both. For example, the `draft` skill tells the agent to write connections made in `main.md` back to the wiki, and `check.py` lists sources that `main.md` cites in one sentence but the wiki does not connect.
- **Evaluation:** the claims checklist, ticked by hand against the sources.
- **Trace:** `wiki/log.md`, with decisions and their reasons, rotated into archives when it grows; `docs/lessons.md` indexes what it taught.

---

## Why not just RAG?

|                   | Classic RAG         | This wiki                      |
|-------------------|---------------------|--------------------------------|
| What's retrieved  | raw chunks          | curated wiki pages             |
| Quality over time | flat                | compounds with each ingest     |
| Storage           | vector DB           | markdown in git                |
| Contradictions    | silently coexist    | surfaced by `lint`             |
| Ownership         | vendor-specific DB  | a git repo you own             |
| Portability       | migrate DB, reindex | `git clone` / local copy       |

---

## Repository layout

```
raw/               source PDFs and supplements (immutable; files are only renamed at ingest)
wiki/
  papers/          one page per ingested paper (firstauthor-year-keyword.md)
  index.md         content catalog — LLM reads this first on every query
  log.md           append-only operation log (older entries in log-archive/)
  references.md    auto-maintained citation list (APA by default)
main.md            evolving paper draft — IMRaD sections, single file; figures as ```mermaid blocks
figures/           the diagrams copied out of main.md (.mmd) and rendered for export (.svg)
notes.md           your own notes (the agent does not edit it)
docs/
  claims-by-source.md  claim checklist per source, plus the register of the author's own inferences
  lessons.md       what went wrong and what changed because of it
  ai-review-brief.md   instructions for an external AI reviewer
  export.md, print.css making the HTML and the PDF
  private/         your private drafts (git-ignored)
scripts/           check.py (consistency check), claim_quotes.py (claims ↔ draft sentences),
                   check_abbreviations.py (abbreviation list ↔ draft),
                   render_pdf_pages.py (PDF text dump and page images),
                   figures.py (diagrams to .mmd and .svg), export.py (build copy for HTML and PDF),
                   rotate_log.py (log archives), eval_skills.py (does each task load its skill);
                   hooks/harness.py holds the hooks
.claude/settings.json  permission rules and the hooks
.claude/skills/    the procedures: ingest, draft, lint (loaded when a task matches);
                   grill-paper (/grill-paper): interview before a decision;
                   grinding (/grinding [wiki] <source>): check one source's claims in main.md or the wiki
AGENTS.md          wiki schema and agent instructions (CLAUDE.md just imports it)
llm-wiki.md        the pattern explained
```

---

## Tips

- **Select a section** in `main.md` and say *"rewrite this"* — the agent edits only that section.
- **`[CITATION NEEDED]`** markers in the draft mean the agent couldn't find a supporting source — add the paper and re-ingest.
- **Check each new source page against the PDF at ingest.** An error caught there is fixed in one place; caught in the draft, it may already be in five.
- **Non-open-access PDFs:** list them by name in `.gitignore` before committing, if the repo is public.
- **Graph view** in Obsidian or Foam shows how paper pages link to concept and gap pages — useful for spotting holes in coverage (settings below).
- **Ask another model family for a review** before publishing: give it `main.md` and `docs/ai-review-brief.md`.
- **Log decisions, not only changes.** Why a source was left out or a search not run is the first thing you will want to know later.
- **`wiki/references.md`** is copy-paste ready for submission; specify your citation style if not APA.

---

## Licences

The scripts in `scripts/` are MIT-licensed ([scripts/LICENSE](scripts/LICENSE)). `.claude/skills/grill-paper` is adapted from Matt Pocock's `grilling` skill (MIT); the other skills in `.claude/skills/` are MIT-licensed like the scripts. `llm-wiki.md` comes from another author and keeps its own terms.

---

## Optional: a viewer with a graph view (Obsidian or VS Code + Foam)

The wiki is plain markdown, so any editor works. A viewer with a graph view and clickable `[[wikilinks]]` makes it much easier to see how the sources connect and to follow what the agent changed. Neither is required.

### Obsidian

[Obsidian](https://obsidian.md/) is a free markdown app with a graph view, backlinks and search built in. Open the repository folder as a vault (**Open folder as vault**); nothing needs to be installed in the repository. Keep the agent in a terminal or in VS Code next to it.

- **Graph view filter:** `path:wiki -file:index -file:log`. The index and the log link to almost every page and would turn the graph into one star around them; `-file:log` also drops the archives in `wiki/log-archive/`.
- **Colour groups, in this order** (a node takes the colour of the first group it matches): `path:wiki/papers` for the paper pages, then `path:wiki` for the concept and method pages. Search syntax: <https://obsidian.md/help/plugins/search>.
- **Tags:** turn on Tags in the graph filters to see the theme tags as nodes; they come from the Tag vocabulary in `AGENTS.md`. A `#word` in prose would become a tag too, which is why the schema asks for `\#` before a hash that is not one.
- Obsidian writes its settings to `.obsidian/` in the folder; add it to `.gitignore` if you do not want them in the repository.

The worked example has a highlighted graph and the exact settings behind it: [docs/images/README.md in MEA_review_llm_wiki](https://github.com/AnaHill/MEA_review_llm_wiki/blob/master/docs/images/README.md).

### VS Code + Foam

[Foam](https://foambubble.github.io/foam/) adds a graph view and `[[wikilink]]` navigation inside VS Code.

1. Install the [Foam extension](https://marketplace.visualstudio.com/items?itemName=foam.foam-vscode) from the VS Code marketplace.
2. Reload the window — Foam will index the `wiki/` files automatically.
3. Open **Foam: Show Graph** from the command palette to explore link relationships between pages.
