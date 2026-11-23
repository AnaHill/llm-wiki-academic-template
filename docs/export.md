# Exporting main.md to HTML and PDF

`main.md` stays the source of the paper. Figures are written as ```mermaid blocks inside it, so that `scripts/claim_quotes.py` can quote claims from inside a diagram; the HTML and the PDF are made from a generated build copy, `main-export.md`, never by hand-editing an exported file. The route is HTML first, then the PDF printed from the HTML by a browser, which handles figures, tables and page breaks better than the usual Markdown-to-PDF converters.

## Figure workflow

- Write or change a diagram in `main.md`, with its caption on an italic line just above it: `*Figure 1. ...*`.
- `python -I scripts/figures.py --render` copies each diagram to `figures/<name>.mmd`, records its hash in `figures/figures.json` and draws `figures/<name>.svg` with a pinned Mermaid version in headless Edge or Chrome (it needs network access once per run to load Mermaid; the diagram is drawn locally). Give each figure a file name in `NAMES` in `scripts/figures.py`.
- `scripts/check.py` warns when a diagram in `main.md` has changed since its image was rendered.
- Do not render in Mermaid Live: its SVG export keeps the preview's theme and scaling.
- Look at the rendered images: no text running out of a box, no literal `\n`, readable label colours.

## Build checklist

Run from the repository root.

1. `python -I scripts/figures.py --render`, if `check.py` says a diagram changed or an image is missing.
2. `python -I scripts/export.py --write` writes `main-export.md`: diagrams replaced by the rendered images with alt text from the caption, a visible title block from the front matter (title, author, date), bare URLs turned into links, HTML comments removed. Add `--date YYYY-MM-DD` to stamp a date other than today, for example the planned publication date.
3. Convert `main-export.md` to HTML with your usual tool (for example the VS Code extension "Markdown PDF": Export (html)). The output appears next to the file.
4. Paste `docs/print.css` into a `<style>` block just before `</head>`, so its rules come after the converter's. In the same `<head>`, replace the converter's `<title>main-export.md</title>` with the paper's title: the browser copies it into the tab and into the Title field of the PDF.
5. Open the HTML in Chrome or Edge, press Ctrl+P, and choose the printer **Save as PDF** (not "Microsoft Print to PDF", which drops the links). Under More settings: paper A4, margins **Default** (the `@page` rule of `print.css` sets them), **Headers and footers off** (no CSS can remove the browser's running header), background graphics on. Save under a short name of your own, for example `Surname-YYYY-short-title.pdf`; the browser otherwise names the file after the title.
6. The browser fills only the Title of the PDF's metadata. Author and Keywords can be added without touching the pages, with PyMuPDF:
   `python -I -c "import fitz; d=fitz.open('<file>.pdf'); m=d.metadata; m['author']='<Name>'; m['keywords']='<keywords>'; d.set_metadata(m); d.saveIncr()"`

The export files (`main-export.md`, `main-export.html`, `main-export.pdf`) are git-ignored; add the name of your final PDF to `.gitignore` too, or deposit it and keep it out of the repository.

## Checks on the finished files

Each of these has failed at least once in the project this template comes from.

- [ ] Every page viewed once: each figure on one page with its caption, each table caption on the same page as its table, no heading alone at the foot of a page.
- [ ] Label text in the figures readable in print (light text on a light fill disappears).
- [ ] Tables within the right margin; formulas rendered as formulas.
- [ ] Search the PDF text for `<!--`, a stray `*`, and an escaped hash: `\#ABC` must print without its backslash.
- [ ] Title, author and date visible at the top; the Title field of the PDF is the paper's title.
- [ ] A DOI in the reference list and any other link open.
- [ ] If the HTML is deposited as well: it loads its figures from `figures/` beside it, so embed them first, or deposit the PDF only (the source text can be archived with a snapshot of the repository).
