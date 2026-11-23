# Lessons from this project

What went wrong or worked during the project, and what changed because of it, gathered by theme from `wiki/log.md` and its archives. The log is the evidence and stays chronological; this file is the index of what it taught. Read it before starting a similar project, not after. A worked example with about thirty lessons is [docs/lessons.md in MEA_review_llm_wiki](https://github.com/AnaHill/MEA_review_llm_wiki/blob/master/docs/lessons.md), the review this template was distilled from; most of what this template does is answered there by the failure that caused it.

Each lesson has three lines:

- **Evidence:** the log entries it rests on, as `log <date> <type>`, which match a `## [<date>] <type> |` header in `wiki/log.md` or its archives in `wiki/log-archive/`. `scripts/check.py` reports a reference that matches no header, so every lesson can be traced to what actually happened. A lesson that the log does not record names its other source instead.
- **Changed:** what was added to the harness because of it (a rule in `AGENTS.md`, a script, a setting, a skill), with the date.
- **Status:** `rule + check` (a rule and a mechanical check that notices when it is broken), `rule only` (written down, but depends on someone remembering it), or `open` (learned, but nothing in the repository enforces or even states it yet). The `open` and `rule only` items are the ones to carry into the next project deliberately.

Add a lesson when a task adds a rule, a check or a limit because something went wrong (see "Decisions go in the log" in `AGENTS.md`). Group lessons under `## ` themes as they accumulate, for example sources and ingest, claims and wording, the draft and its summaries, tools and checks, working with the agent.

<!-- Example lesson (delete when the first real one is added):

## 1. Sources and ingest

### Take every bibliographic detail from the source itself
The first draft had a fabricated author list for one paper, which reached the reference list before it was noticed.
- **Evidence:** log 2026-06-17 init
- **Changed:** "Never invent citations, authors, or facts" in `AGENTS.md`; `check.py` warns when a paper page's first author differs from its reference key
- **Status:** rule + check
-->
