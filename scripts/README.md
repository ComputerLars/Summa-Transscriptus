# Book production

Install the Typst CLI (0.15 or newer) and the Python packages in requirements-pdf.txt. From the repository root, run:

    python scripts/build_book_pdf.py

The script reads the current archival texts and image records, prepares the local .book-build directory, and compiles scripts/book.typ. The published PDF keeps its established path. TYPST_BIN can specify the Typst executable.

Typography and page construction live in book.typ; the Python builder supplies structured content. Fonts in assets/fonts are available for portable builds. The defence edition uses the installed Microsoft Garamond and Consolas families when available in PowerPoint’s DFonts directory, with EB Garamond and DejaVu Sans Mono as fallbacks. Font files from Microsoft Office are not redistributed in this repository.
