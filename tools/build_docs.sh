#!/usr/bin/env bash
# Build the manuals from docs/*.md:
#   .docx  - editable Word file with native Word equations (pandoc)
#   .pdf   - print version (pandoc -> HTML/MathML -> Chromium)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/docs"
for md in *.md; do
  [ "$md" = "README.md" ] && continue
  base="${md%.md}"
  pandoc "$md" -o "$base.docx" --resource-path=. --toc --toc-depth=2
  pandoc "$md" -s --mathml --toc --toc-depth=2 --css "$ROOT/tools/doc_style.css" --embed-resources \
         --resource-path=. -o "/tmp/$base.html"
  node "$ROOT/tools/html_to_pdf.js" "/tmp/$base.html" "$base.pdf"
  echo "built docs/$base.docx docs/$base.pdf"
done
