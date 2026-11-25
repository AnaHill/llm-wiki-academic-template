# AGENTS.md

Guidance for the coding agent (Claude Code, Codex or similar) in this repository: an LLM-maintained academic wiki behind one paper. The researcher curates sources and makes the decisions; you keep the wiki and draft the paper. `CLAUDE.md` only imports this file. The pattern is in [llm-wiki.md](llm-wiki.md) (read it when starting a new session); what the repository does and why is in [README.md](README.md).

## Layout

- `raw/` — source documents (PDFs, supplements).
- `wiki/` — yours: `papers/` (one page per source), concept, method and gap pages, `index.md` (catalog; read it first), `log.md` (append-only log; when `check.py` warns that it passed 40 kB, `python -I scripts/rotate_log.py --write` moves the oldest entries to `log-archive/`), `references.md` (APA list of every ingested source).
- `main.md` — the paper: one file, IMRaD sections as `#` headings, figures as ```mermaid blocks, a `# References` list at the end. Do not restructure it unless asked.
- `notes.md` — the researcher's own thinking.
- `docs/` — process documentation, not part of the wiki: `claims-by-source.md` (the claims of `main.md` per source and the register of the author's own inferences), `lessons.md`, `ai-review-brief.md`, `export.md` and `print.css`, literature search records. Edit `docs/private/` (git-ignored private drafts) only when asked.
- `scripts/` — check and build scripts; each describes itself in its docstring. `scripts/hooks/harness.py` holds the hooks in `.claude/settings.json`, which also holds the permission rules; `scripts/eval_skills.py` checks that each task still loads its skill.
- `figures/` (diagrams copied out of `main.md` and rendered), `figure_analysis/` (regenerable PDF dumps, git-ignored), `main-export.md` (generated build copy of `main.md`, git-ignored; never edit it).

## Procedures

The steps of each operation are in `.claude/skills/<name>/SKILL.md`. Claude Code loads them by itself; with another agent, read the file before starting the task.

| When | Skill |
|------|-------|
| the researcher adds sources to `raw/` and asks to process or check them | `ingest` |
| writing or revising `main.md` or `docs/claims-by-source.md` | `draft` |
| the researcher asks for a health check | `lint` |
| `/grill-paper`: interview before a decision (only when called) | `grill-paper` |
| `/grinding <source>`: claim-by-claim check of `main.md` against a source; `/grinding wiki <source>`: the same for the wiki, right after ingest (only when called) | `grinding` |

To answer a question, read `wiki/index.md` and `notes.md`, drill into the relevant pages and answer with citations; offer to file a substantial comparison or synthesis as a new wiki page.

To search for literature, record the search in `docs/` (e.g. `docs/<topic>-search.md`) so that any statement about it in `main.md` rests on a real record: databases, exact queries, dates, record counts, citation chasing, what was not searched, and why candidates were selected or rejected. Report the candidates before ingesting any (the verify-first pass of `ingest`). Never describe a search in the paper that was not recorded.

## Rules that always apply

- **Never invent citations, authors, or facts.** If an author list, DOI, venue or finding cannot be verified from the source itself (PDF, HTML or a reliable secondary confirmation), say so and mark it unverified rather than filling the gap plausibly. Known failure modes in LLM-assisted papers: fabricated author lists for real papers, wholly invented papers that look plausible, and plausible-sounding method statements ("a targeted search of database X on date Y") with no record behind them. An uncorroborated bibliographic detail is a stop-and-flag case, not a best-guess case.
- **`raw/` is immutable.** Never edit or delete a source; the only change allowed is renaming a file at ingest.
- **`notes.md` is the researcher's.** Never edit it, and never turn its content into wiki pages as if it were sourced fact. When you use it, say so ("your note of 2026-10-15") and keep it distinct from claims backed by `wiki/papers/`. If the researcher wants a thought kept, write it in the chat, dated and ready to paste; they add it themselves.
- **No stray tags.** If the wiki is read in Obsidian, `#word` in prose becomes a tag; tags belong only in the `tags:` front matter. In every markdown file, `wiki/log.md` and `main.md` included, write a hash-prefixed identifier that is not a tag with a backslash escape (`\#AB01`), keeping it as the source writes it; not with quotes, a bare hash or a dropped hash. It displays as "#AB01", and Pandoc prints it without the backslash. `check.py` warns about unescaped hashes.
- **Tag vocabulary.** Tags in the `tags:` front matter come from this fixed list, so that the Obsidian graph groups pages by theme instead of showing one-off tag nodes. Theme tags follow the sections of `main.md`; add them here as the paper takes shape. Page-type tags: `type/concept`, `type/method`, `type/analysis` (pages outside `wiki/papers/`), `type/review` (review or perspective papers). Two to four tags per page; add a tag here only when it fits at least three pages.
- **References.** `wiki/references.md` lists every ingested source in APA (unless the researcher names another style), one entry per line, sorted by first-author surname. The year is the issue year once volume and pages exist, not the online-first year, even when the publisher's citation tool gives the earlier one; the paper page records both dates. The final style follows the target venue and is applied at the end, so do not convert entries before then. The `# References` list of `main.md` holds exactly the entries cited there, each a verbatim copy of its line in `wiki/references.md` (which may hold more): never edit one copy without the other.
- **Decisions go in the log.** Each `wiki/log.md` entry starts `## [YYYY-MM-DD] <type> | <subject>`, with type `ingest`, `query`, `draft`, `lint` or `grill`, so the log stays grep-parseable. A decision and its reasons (what to cite or leave out, why a search was or was not run, which option was declined) get an entry even when nothing else changes; a decision recorded only in a to-do list is lost when the list is deleted. When a task adds a rule, a check or a limit because something went wrong, also add a lesson to `docs/lessons.md` (evidence as `log <date> <type>`, which `check.py` verifies, what changed, and a status). To search the history, grep `wiki/log.md wiki/log-archive/`.
- **Finish with the checks.** Before ending a task that changed `wiki/` or `main.md`, run `python -I scripts/check.py` and fix every ERROR, or tell the researcher why not; it cannot verify that author lists or findings are true, which still needs the source. After editing `main.md` also run `check_abbreviations.py` and `claim_quotes.py --check`; Claude Code's hook does this after its own Edit and Write, but not after a change made by a shell command or by another agent.
- **Commit messages** (the researcher's preference; change or delete this line freely): propose one line, lowercase, in the present tense, completing "In this commit, I …", alone in a code block, with no body or trailer. The researcher commits.
- **Surgical and minimal.** State assumptions; ask when a source's relevance or a request is ambiguous. Change only what the request or the new source warrants. Don't create pages speculatively: note a concept inline where it first appears, and give it a page of its own when it recurs or becomes central.

## Schema evolution

This file is the schema of the wiki; update it with the researcher as conventions evolve (for a new paper, start by tailoring the Tag vocabulary). Keep here only what applies to every task, and put a procedure in a skill. When a rule is absolute and mechanical, also enforce it in `.claude/settings.json` (permission rule or hook), and pair every important convention with a check in `scripts/check.py` where a script can decide it: a rule alone gets forgotten, and a script alone cannot judge.
