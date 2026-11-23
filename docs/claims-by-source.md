# Claims in main.md, by source

A checklist for verifying the paper against its sources. Each source has a section listing every claim that `main.md` attributes to it, numbered, with the section tag in brackets; tick `[x]` when you have checked the claim against the source. The tag is the start of the `main.md` heading the claim sits in (e.g. `[Introduction]`, `[Related Work]`); `scripts/claim_quotes.py` uses it to attach the matching sentences of `main.md` below each claim.

Section headings name the source as it is cited in `main.md`: `## Smith et al. (2023)`, `## Smith & Jones (2023)` or `## Smith (2023)`, optionally followed by more text.

<!-- Example (delete when the first real source is added):

## Smith et al. (2023)

Local file: `raw/smith-2023-keyword.pdf`; page `wiki/papers/smith-2023-keyword.md`. Status: not yet checked.

Claims (tick `[x]` when you have checked the claim against the source):

- [ ] (1) [Introduction] the method is widely used for X.
- [ ] (2) [Related Work] it reports a 20 % improvement over baseline Y.
-->

## Register of the author's own inferences

These are statements in `main.md` that no single reference supports: generalisations from one or two studies, reasoned steps beyond what any source says, and the author's hypotheses. `main.md` does not mark them in the text, so this list is their only record; every new unsourced statement in `main.md` needs an item here. Tick `[x]` when you have decided that you stand behind the wording.

Reading guide for each item: **bold** = the item's topic and the `main.md` section tag in brackets; **Text:** = the wording in `main.md`, in double quotes (`scripts/claim_quotes.py` reports a quoted wording that `main.md` no longer contains; when the wording changes, update the quote and keep the old one in parentheses as history); **Based on** = the sources behind it; **Support** = where the statement's warrant comes from, one of:

- `sourced` — a source states this directly, and the evidence behind it carries the wording used.
- `thin` — a source states it, but on one or two studies, so the risk is that it does not generalise.
- `inference` — no source states it, but it follows by a reasoned step from what sources do state. The risk is in the step, not in the sources: the item can fail although every source is right.
- `opinion` — a judgement or a preference of the author, not a claim about the world that a source could settle.
- `none` — no source supports it at all: a hypothesis or an idea of the author's own, and `main.md` says so where it appears.
- `inherited` — the item summarises other items and takes their support (for example the Highlights).

These are not points on one scale. `thin` is sourced but narrow; `inference` is not sourced as such but derived; they fail in different ways and need different fixes, a better study for the first and a better argument for the second. Every Support line carries at least one of these six values, and `scripts/check.py` warns about a line that carries none or that introduces a seventh; add a value only by editing this list and `SUPPORT_VALUES` in `scripts/check.py`.

<!-- Example item (delete when the first real item is added):

- [ ] **1. [Discussion]** the gap limits comparison between laboratories
  - **Text:** "this gap plausibly limits comparison between laboratories"
  - **Based on:** Smith et al. (2023); Lee (2024)
  - **Support:** `inference` — both report differing definitions; that this limits comparison is the step taken here
-->

