# Brief for an AI reviewer of `main.md`

Give this file to the reviewing model together with `main.md`, and nothing else. `main.md` is self-contained: it holds the full text, the figures and the reference list. Fill in the bracketed parts before use, and delete what does not apply. A second model family (not the one that helped write the paper) gives the most independent read.

---

## What you are reviewing

*[One paragraph: the kind of paper (for example a narrative review by a single author), its topic, the period it covers, where it will be published (preprint, journal), and anything that sets its scope (no new experiments, an unfunded personal project).]*

Figures written as fenced ```mermaid code blocks are diagrams; read them as diagrams, not as code to be corrected.

## What the paper already says about itself

Do not spend the review restating these. They are stated in the text, and a finding that repeats one of them tells the author nothing.

- *[The declared limitations, one per line: how the sources were selected, how many authors and whether there was independent screening, any competing interest such as the author's own earlier work used as a framework, statements that rest on one or two studies, which sections are speculative.]*

*[If every claim attributed to a source has already been checked against that source (see `docs/claims-by-source.md`), say so here, so that "verify the citations" is not taken as the useful task.]*

## What would be most useful

In rough order of value:

1. **Claims that overreach their evidence.** Places where the wording is stronger than what the cited work can carry, where a condition of the source is dropped, or where a generalisation rests on a single study without saying so.
2. **Missing literature that would change a conclusion.** Not a reading list: a work that contradicts a claim, supersedes a cited source, or fills a gap the paper says is open. For each, say which sentence it affects and how.
3. **Whether the main conclusions hold up.** *[Name them: for example the gaps the paper identifies.]* Are they distinct, open, and supported by the material presented?
4. **Whether the argument carries.** Does the Introduction set up what the Conclusion delivers? Is any section doing no work? Is anything important asserted but never returned to?
5. **Internal inconsistencies.** A statement in one section that another contradicts, including between the text, the tables and the figures, and between the Abstract or Highlights and the body.

## What is not useful here

- Recommending a different kind of paper (for example a systematic review) when the scope is declared.
- Journal formatting, reference style, word counts, section-heading conventions.
- Asking for new experiments or data, if the paper reports none.
- Line edits for style, unless the wording changes the meaning of a claim.

## Rules for any reference you suggest

A suggested reference that cannot be verified is worse than none: invented citations are the most common way an AI-assisted paper goes wrong.

- Give the **DOI** for every work you propose, with the author list, year, title and venue.
- State **how you know it exists**: an indexed record you retrieved, or your training data. Say which.
- If you are not certain a work exists as you describe it, either leave it out or mark it clearly as unverified. Do not reconstruct a plausible citation.
- Prefer naming a specific finding in the work and the sentence of `main.md` it bears on, rather than a general topic.

## How to return your review

Return your **entire response inside one markdown code block**, fenced with four backticks, so that it can be pasted into a file unchanged. Use this structure:

````markdown
## Verdict

Two or three sentences: is the paper sound as it stands, and what is the single most important thing to fix?

## Findings

### 1. <short title> — <major | moderate | minor>
**Where:** the section, and the sentence quoted well enough to find it.
**Problem:** what is wrong, in one or two sentences.
**Suggestion:** a concrete replacement wording, or the specific thing to check.

### 2. ...

## Suggested references (if any)

| Work (authors, year, title, venue) | DOI | How verified | Which sentence it affects | Why it matters |
|---|---|---|---|---|

## What I checked and could not fault

A short list, so the author knows what the review covered rather than only what it objected to.
````

Rank the findings most important first. A short review of real problems is more useful than a long one padded with observations.
