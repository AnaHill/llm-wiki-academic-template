---
name: grill-paper
description: Relentless interview to settle a research decision before acting on it, such as the scope of a section, how strongly to state a claim, which sources to ingest or cite, or which lint findings to fix. Facts come from the wiki and the sources; decisions stay with the researcher.
disable-model-invocation: true
license: MIT
---

# Grill paper

Adapted from the `grilling` skill by Matt Pocock (https://github.com/mattpocock/skills, MIT licence) for an LLM-maintained academic wiki. Read AGENTS.md first; its rules (never invent citations, notes.md is read-only, surgical changes) apply throughout.

Interview the researcher until you reach a shared understanding of the decision in front of you. Do not draft, ingest or edit anything during the session.

## The argument tree

Map the topic as an **argument tree**: every decision branches into the decisions that hang off it. Typical levels, top to bottom:

1. **Question or claim** — what the section, paragraph or choice is meant to establish.
2. **Evidence** — which sources support it, how directly, and what the closest contrary or competing work is.
3. **Scope** — period, model systems, platforms, what is deliberately left out.
4. **Strength and wording** — how firmly the claim can be stated, and which parts are the researcher's own inference rather than a finding of a source.

A settled claim opens questions about its evidence; settled evidence opens questions about scope and wording. A question whose answer depends on another still-open question waits for a later round.

## Rounds

Work the tree in rounds. The **frontier** is every decision whose prerequisites are already settled. Ask the whole frontier in one round: number each question and give your recommended answer, with the reason in one or two sentences. Then wait for the answers before the next round.

```
❓ **Q1** – **<question title>**: <question, with options if there are several>

➡️ <recommended answer and why>

---

❓ **Q2** – …
```

Word each question so that "yes" accepts your recommendation. Write in the researcher's language. Each round of answers reshapes the tree: recompute the frontier and ask the next round.

## Facts are your job, decisions are the researcher's

- **Look facts up; never ask the researcher for something the repository can tell you.** Start from `wiki/index.md`, then `wiki/papers/`, concept and method pages, `docs/`, `main.md` and, when a page is not enough, the source in `raw/` (text dumps in `figure_analysis/`). Read `notes.md` for the researcher's own views and cite it as theirs ("your note of …"). For a lookup that needs many files, dispatch a sub-agent with a fresh context; while it runs, ask the questions that do not depend on it.
- **When the evidence is not there, say so.** Report that no page supports the point and offer the options: a literature search, a `[CITATION NEEDED]` mark, weaker wording, or dropping the claim. Never fill the gap with a plausible source, author list, DOI or finding.
- **Say where a fact came from** (page, source and page number), so the researcher can check it, and say when a wiki page and its source disagree.
- **Decisions are the researcher's**: what to claim and how strongly, the scope, which sources to include or exclude, whether an inference of the author goes into the paper. Put each to them and wait.

## Ending

The session is done when the frontier is empty: every branch visited, nothing left silently assumed. Then:

1. Summarise the settled decisions as a numbered list, each with its reason and its source (wiki page or the researcher's answer).
2. Ask the researcher to confirm that this is the shared understanding.
3. After confirmation, offer — do not perform — the follow-up: a `wiki/log.md` entry `## [YYYY-MM-DD] grill | <topic>` with the decision list; for a larger decision (for example a literature search or a source selection) a separate file in `docs/`; and the operation the decisions lead to (Draft, Ingest, Lint fixes), run under its own AGENTS.md rules. Own inferences that will appear in `main.md` go to the register in `docs/claims-by-source.md`, not as labels in the paper.

## When not to use it

Mechanical work with no open choice (ingesting a source already selected, fixing a broken link, running `scripts/check.py`). If a question can only be answered by seeing a draft, say so and suggest drafting a short throwaway version first.
