#!/bin/bash

# Fail immediately if any command fails
set -e

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <input_file_path> <output_directory>"
  exit 1
fi

INPUT_FILE="$1"
OUTPUT_DIR="$2"

# Step 1: Perform OCR and save the result to the directory
echo "Performing OCR on $INPUT_FILE..."
python -m content_extraction.do_ocr "$INPUT_FILE" -o "$OUTPUT_DIR"

# Step 2: Combine the OCR pages into a single file
echo "Combining pages into a single Markdown file..."
cd "$OUTPUT_DIR"
ls page-*.md | sort | xargs -I{} sh -c 'cat "{}"; echo; echo' > combined.md

# Step 3: Extract headings from the combined Markdown file
echo "Extracting headings from combined.md..."
grep "^#" combined.md > headings.md

# Step 4: Fix any OCR errors using provided script
echo "Fixing OCR errors..."
fixed_text=$(python -m content_extraction.fix_ocr combined.md headings.md)
echo "$fixed_text" > fixed.md

# Step 5: Render the markdown file to HTML
pandoc fixed.md -s -f markdown -t html -o index.html

echo "All processes completed successfully. Output saved in $OUTPUT_DIR"
