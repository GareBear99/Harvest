TRADING SYSTEM DOCUMENTATION PACKAGE
====================================

This package contains comprehensive documentation for the trading system.

FILES INCLUDED:

1. USER_MANUAL.md
   - Complete system guide
   - Usage instructions
   - Troubleshooting
   - Command reference
   
2. MATHEMATICS.md
   - Mathematical explanations
   - Simple examples with real numbers
   - Trading calculations
   - Performance metrics
   
3. TRON_INTEGRATION.md
   - Future enhancement plans
   - Tron blockchain integration roadmap
   - Technical architecture
   - Timeline and milestones

FORMATS:

- .md files can be viewed in any text editor or markdown viewer
- If pandoc was available during generation, PDF versions are included
- HTML versions can be opened in any web browser

VIEWING OPTIONS:

Markdown (.md):
- GitHub, GitLab (automatic rendering)
- VS Code (with Markdown Preview)
- Typora, MacDown, or any markdown editor
- Any text editor (raw format)

PDF (.pdf):
- Adobe Acrobat Reader
- Preview (macOS)
- Any PDF viewer

HTML (.html):
- Chrome, Firefox, Safari, Edge
- Any web browser

GENERATING PDFS:

If PDF files are not included, you can generate them:

1. Install pandoc:
   macOS:   brew install pandoc
   Linux:   sudo apt install pandoc
   Windows: https://pandoc.org/installing.html

2. Run this script again from the main directory:
   ./generate_docs.sh

3. PDFs will be created in this package

SUPPORT:

For questions or issues:
1. Check USER_MANUAL.md Troubleshooting section
2. Run: python pre_trading_check.py (system health check)
3. Review archive documentation in docs/archive/

Last Updated: December 17, 2024
