r'''
Render PDF pages to PNG images so they can be visually inspected (e.g. by Claude
Code's Read tool, which can view images but not PDFs directly).

Usage:
python scripts/render_pdf_pages.py raw\some-paper.pdf
-> auto-detects pages containing "figure"/"fig."/"table" captions and renders
   just those pages to .\figure_analysis\<pdf-name>\page_<N>.png

python scripts/render_pdf_pages.py raw\some-paper.pdf --pages 2,5-7
-> renders only the specified pages (1-indexed), ignoring auto-detection

python scripts/render_pdf_pages.py raw\some-paper.pdf --pages all -o custom_output --dpi 300
-> renders every page, at 300 DPI, into .\custom_output\<pdf-name>\

python scripts/render_pdf_pages.py raw\some-paper.pdf --text
-> writes the full text, with "===== PAGE N =====" markers, to
   .\figure_analysis\<pdf-name>\text.txt and renders NOTHING (use this first when the
   Read tool cannot open the PDF). Add --pages (e.g. --text --pages 3,5) to also render pages.
'''

import argparse
import os
import fitz  # PyMuPDF

DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "figure_analysis")
FIGURE_PATTERNS = ['figure', 'fig.', 'fig ', 'table']
DEFAULT_DPI = 200


def detect_figure_pages(doc):
    pages = set()
    for page_num in range(len(doc)):
        text = doc[page_num].get_text().lower()
        if any(pattern in text for pattern in FIGURE_PATTERNS):
            pages.add(page_num + 1)
    return sorted(pages)


def parse_pages(spec, page_count):
    if spec is None or spec.lower() == 'all':
        return list(range(1, page_count + 1))

    pages = set()
    for part in spec.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-')
            pages.update(range(int(start), int(end) + 1))
        else:
            pages.add(int(part))
    return sorted(p for p in pages if 1 <= p <= page_count)


def write_text(doc, page_output_dir):
    out_path = os.path.join(page_output_dir, "text.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        for page_num in range(len(doc)):
            f.write(f"===== PAGE {page_num + 1} =====\n{doc[page_num].get_text()}\n")
    print(f"Wrote text of {len(doc)} page(s) to {out_path}")


def render_pages(pdf_path, output_dir, pages_spec, dpi, text=False):
    doc = fitz.open(pdf_path)
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    page_output_dir = os.path.join(output_dir, pdf_name)
    os.makedirs(page_output_dir, exist_ok=True)

    if text:
        write_text(doc, page_output_dir)
        if pages_spec is None:
            doc.close()
            return []

    if pages_spec is None:
        pages = detect_figure_pages(doc)
        print(f"Auto-detected {len(pages)} page(s) with figure/table captions: {pages}")
    else:
        pages = parse_pages(pages_spec, len(doc))

    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    written = []
    for page_num in pages:
        pix = doc[page_num - 1].get_pixmap(matrix=matrix)
        out_path = os.path.join(page_output_dir, f"page_{page_num}.png")
        pix.save(out_path)
        written.append(out_path)

    doc.close()
    print(f"Rendered {len(written)} page(s) to {page_output_dir}")
    return written


def main():
    parser = argparse.ArgumentParser(description="Render PDF pages to PNG for visual inspection.")
    parser.add_argument("pdf_path", help="Path to the input PDF file")
    parser.add_argument("-o", "--output-dir", default=DEFAULT_OUTPUT_DIR,
                         help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--pages", default=None,
                         help="Pages to render: 'all', a list like '2,5-7', or omit to "
                              "auto-detect pages containing figure/table captions")
    parser.add_argument("--dpi", type=int, default=DEFAULT_DPI,
                         help=f"Render resolution in DPI (default: {DEFAULT_DPI})")
    parser.add_argument("--text", action="store_true",
                         help="Also write the full text to <output>/<pdf-name>/text.txt; "
                              "without --pages this skips page rendering")
    args = parser.parse_args()

    render_pages(args.pdf_path, args.output_dir, args.pages, args.dpi, args.text)


if __name__ == "__main__":
    main()
