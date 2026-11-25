---
name: lint
description: Health check of the wiki and the draft - contradictions, stale claims, orphan pages, missing concept pages and cross-references, unsupported claims in main.md - with the output of scripts/check.py, as one prioritized list; read-only until the researcher approves fixes. Use when the researcher asks for a lint, health check, audit or consistency review.
license: MIT
---

# Lint

The rules of AGENTS.md apply throughout. Change nothing until the researcher approves fixes.

## Look for

- contradictions between pages, and stale claims superseded by newer sources;
- orphan pages (no inbound links), concepts mentioned but lacking a page of their own, missing cross-references;
- claims in `main.md` that no page in `wiki/` backs, and unsourced statements missing from the register in `docs/claims-by-source.md`;
- connections `main.md` makes that the wiki does not carry: every section of `main.md` with several sources has a concept page, paper pages link the concept pages that cite them, tags follow the Tag vocabulary;
- questions worth asking next, missing papers, and sources that would fill visible gaps.

Run `python -I scripts/check.py` (it reports the mechanical part; include its output in the report) and `python -I scripts/claim_quotes.py` (read its Notes).

## Report

One prioritized list: script errors, then your own judgement findings, then script warnings, then suggestions. Give each finding its file and, where it helps, a proposed fix. Offer to append a `## [YYYY-MM-DD] lint | <scope>` log entry; for a large audit, offer an audit file in `docs/` (as `docs/lint-fixes-<date>.md`).

## When the researcher approves fixes

Apply only the fixes named. A fix to `main.md` or `docs/claims-by-source.md` follows the `draft` skill; a fix to a paper page keeps the page format of the `ingest` skill. Append a `## [YYYY-MM-DD] lint | <what was fixed>` log entry and run `python -I scripts/check.py`.
