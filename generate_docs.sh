#!/bin/bash
# Documentation Generation Script
# Generates professional documentation package from markdown sources

set -e

echo "================================"
echo "Documentation Generator"
echo "================================"
echo ""

# Check if pandoc is installed
if command -v pandoc &> /dev/null; then
    HAS_PANDOC=true
    echo "✅ Pandoc detected"
else
    HAS_PANDOC=false
    echo "⚠️  Pandoc not installed (PDF generation not available)"
    echo "   Install with: brew install pandoc (macOS)"
    echo "   Or visit: https://pandoc.org/installing.html"
fi

# Create output directory
mkdir -p documentation_package
echo ""
echo "📁 Creating documentation package..."

# Copy markdown files
echo "  Copying USER_MANUAL.md..."
cp USER_MANUAL.md documentation_package/

echo "  Copying MATHEMATICS.md..."
cp MATHEMATICS.md documentation_package/

echo "  Copying TRON_INTEGRATION.md..."
cp TRON_INTEGRATION.md documentation_package/

# Create README for package
cat > documentation_package/README.txt << 'EOF'
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
EOF

echo "  Created package README.txt"

# Generate HTML versions (always possible)
echo ""
echo "🌐 Generating HTML versions..."

for file in USER_MANUAL MATHEMATICS TRON_INTEGRATION; do
    if [ -f "${file}.md" ]; then
        echo "  Converting ${file}.md to HTML..."
        
        # Simple HTML with styling
        cat > "documentation_package/${file}.html" << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${file}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
            background: #f9f9f9;
        }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; border-bottom: 2px solid #95a5a6; padding-bottom: 8px; }
        h3 { color: #555; margin-top: 20px; }
        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            font-size: 0.9em;
        }
        pre {
            background: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            font-size: 0.9em;
        }
        pre code {
            background: transparent;
            color: #ecf0f1;
            padding: 0;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            background: white;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #3498db;
            color: white;
        }
        tr:nth-child(even) { background-color: #f2f2f2; }
        blockquote {
            border-left: 4px solid #3498db;
            margin: 20px 0;
            padding-left: 20px;
            color: #555;
            font-style: italic;
        }
        .content {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        a { color: #3498db; text-decoration: none; }
        a:hover { text-decoration: underline; }
        hr { border: none; border-top: 2px solid #ecf0f1; margin: 40px 0; }
        @media print {
            body { background: white; }
            .content { box-shadow: none; }
            a { color: #000; }
        }
    </style>
</head>
<body>
    <div class="content">
EOF

        # Use python to convert markdown to basic HTML (if python-markdown is available)
        if command -v python3 &> /dev/null && python3 -c "import markdown" 2>/dev/null; then
            python3 << PYTHON
import markdown
with open('${file}.md', 'r') as f:
    md_text = f.read()
html = markdown.markdown(md_text, extensions=['tables', 'fenced_code', 'codehilite'])
with open('documentation_package/${file}.html', 'a') as f:
    f.write(html)
PYTHON
        else
            # Fallback: just wrap markdown in pre tags (readable but not formatted)
            echo "<pre>" >> "documentation_package/${file}.html"
            cat "${file}.md" >> "documentation_package/${file}.html"
            echo "</pre>" >> "documentation_package/${file}.html"
        fi
        
        cat >> "documentation_package/${file}.html" << EOF
    </div>
</body>
</html>
EOF
    fi
done

# Generate PDFs if pandoc is available
if [ "$HAS_PANDOC" = true ]; then
    echo ""
    echo "📄 Generating PDF versions..."
    
    for file in USER_MANUAL MATHEMATICS TRON_INTEGRATION; do
        if [ -f "${file}.md" ]; then
            echo "  Converting ${file}.md to PDF..."
            pandoc "${file}.md" \
                -o "documentation_package/${file}.pdf" \
                --pdf-engine=wkhtmltopdf \
                -V geometry:margin=1in \
                -V fontsize=11pt \
                -V linkcolor=blue \
                --toc \
                --toc-depth=2 \
                -s \
                2>/dev/null || {
                    echo "    ⚠️  PDF generation failed for ${file} (wkhtmltopdf may not be installed)"
                    echo "       Install with: brew install wkhtmltopdf (macOS)"
                }
        fi
    done
else
    echo ""
    echo "⚠️  Skipping PDF generation (pandoc not available)"
    echo ""
    echo "To generate PDFs:"
    echo "  1. Install pandoc: brew install pandoc (macOS)"
    echo "  2. Install wkhtmltopdf: brew install wkhtmltopdf (macOS)"
    echo "  3. Run this script again"
fi

# Create a combined HTML index
echo ""
echo "📋 Creating index page..."
cat > documentation_package/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading System Documentation</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            background: white;
            color: #333;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }
        h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .version {
            color: #999;
            font-size: 0.9em;
            margin-bottom: 30px;
        }
        .doc-card {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
            transition: transform 0.2s;
        }
        .doc-card:hover {
            transform: translateX(5px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .doc-card h2 {
            margin-top: 0;
            color: #667eea;
        }
        .doc-card p {
            color: #666;
            line-height: 1.6;
        }
        .doc-links {
            margin-top: 15px;
        }
        .doc-links a {
            display: inline-block;
            padding: 8px 16px;
            margin-right: 10px;
            margin-top: 5px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 0.9em;
            transition: background 0.2s;
        }
        .doc-links a:hover {
            background: #5568d3;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            text-align: center;
            color: #999;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Trading System Documentation</h1>
        <p class="version">Version 2.0 | December 17, 2024</p>
        
        <div class="doc-card">
            <h2>📖 User Manual</h2>
            <p>Complete system guide with usage instructions, troubleshooting, and command reference. Start here if you're new to the system.</p>
            <div class="doc-links">
                <a href="USER_MANUAL.html">View HTML</a>
                <a href="USER_MANUAL.md">View Markdown</a>
                <a href="USER_MANUAL.pdf">Download PDF</a>
            </div>
        </div>
        
        <div class="doc-card">
            <h2>🔢 Mathematics</h2>
            <p>Mathematical explanations in simple terms with real examples. Learn how win rate, P&L, leverage, and all calculations work.</p>
            <div class="doc-links">
                <a href="MATHEMATICS.html">View HTML</a>
                <a href="MATHEMATICS.md">View Markdown</a>
                <a href="MATHEMATICS.pdf">Download PDF</a>
            </div>
        </div>
        
        <div class="doc-card">
            <h2>🚀 Tron Integration</h2>
            <p>Future enhancement plans for Tron blockchain integration. Includes technical architecture, timeline, and implementation roadmap.</p>
            <div class="doc-links">
                <a href="TRON_INTEGRATION.html">View HTML</a>
                <a href="TRON_INTEGRATION.md">View Markdown</a>
                <a href="TRON_INTEGRATION.pdf">Download PDF</a>
            </div>
        </div>
        
        <div class="footer">
            <p>For support: Run <code>python pre_trading_check.py</code> from the main directory</p>
            <p>Last updated: December 17, 2024</p>
        </div>
    </div>
</body>
</html>
EOF

# Package everything
echo ""
echo "📦 Creating distribution archive..."
tar -czf trading_system_documentation.tar.gz documentation_package/
echo "  Created trading_system_documentation.tar.gz"

echo ""
echo "================================"
echo "✅ Documentation Generation Complete!"
echo "================================"
echo ""
echo "Generated files:"
echo "  📁 documentation_package/"
echo "     - USER_MANUAL.md"
echo "     - MATHEMATICS.md"
echo "     - TRON_INTEGRATION.md"
echo "     - USER_MANUAL.html"
echo "     - MATHEMATICS.html"
echo "     - TRON_INTEGRATION.html"
echo "     - index.html (main entry point)"
echo "     - README.txt"
if [ "$HAS_PANDOC" = true ]; then
    echo "     - USER_MANUAL.pdf"
    echo "     - MATHEMATICS.pdf"
    echo "     - TRON_INTEGRATION.pdf"
fi
echo ""
echo "  📦 trading_system_documentation.tar.gz (archive)"
echo ""
echo "To view:"
echo "  1. Open documentation_package/index.html in your browser"
echo "  2. Or open any individual .html file"
if [ "$HAS_PANDOC" = true ]; then
    echo "  3. Or open any .pdf file"
fi
echo ""
echo "To share:"
echo "  Send the trading_system_documentation.tar.gz file"
echo ""
