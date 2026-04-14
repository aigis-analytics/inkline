Generate a slide deck from the provided content.

$ARGUMENTS

Steps:
1. If a file path is mentioned, parse it (pandoc for .docx, pymupdf for .pdf, read directly for .md/.txt)
2. Extract key sections, metrics, and structure from the content
3. Build a sections[] list using the section types in CLAUDE.md
4. Use DesignAdvisor(mode="llm") to design the deck
5. Export to ~/.local/share/inkline/output/deck.pdf
6. Print the slide list and announce "PDF ready: ~/.local/share/inkline/output/deck.pdf"
7. Ask the user if they want any changes

Follow all conventions in CLAUDE.md exactly.
