# HTML Content Extraction Tool

A powerful command-line tool for extracting structured content from HTML documents. Converts HTML sections into hierarchical JSON data while preserving formatting, links, and semantic structure.

## Features

- **Hierarchical Parsing**: Automatically detects heading levels and creates nested section structures
- **HTML Preservation**: Maintains original formatting, links, and semantic elements
- **Smart Element Filtering**: Includes meaningful content while filtering out irrelevant elements
- **Flexible Input/Output**: Read from files or stdin, output to files or stdout
- **Section Support**: Works with existing `<section>`, `<article>`, and `<main>` elements
- **Custom Headings**: Supports both standard headings (`h1`-`h6`) and custom headings with `aria-level`

## Installation

```bash
# Install dependencies
pip install beautifulsoup4

# Clone or download this repository
git clone <repository-url>
cd content-extraction
```

## Usage

### Basic Usage

```bash
# Parse HTML file and output to stdout
python main.py example.html

# Parse with pretty-printed JSON
python main.py --pretty example.html

# Save output to file
python main.py example.html -o output.json

# Read from stdin
cat example.html | python main.py --pretty

# Verbose mode with debug information
python main.py --verbose example.html
```

### Command Line Options

```
usage: main.py [-h] [-o FILE] [--pretty] [-v] [--version] [input_file]

Extract structured content from HTML documents

positional arguments:
  input_file         Input HTML file (if not provided, reads from stdin)

options:
  -h, --help         show this help message and exit
  -o, --output FILE  Output JSON file (if not provided, writes to stdout)
  --pretty           Pretty-print JSON output with indentation
  -v, --verbose      Show verbose output and debug information
  --version          show program's version number and exit
```

## Output Format

The tool outputs JSON with the following structure:

```json
{
  "title": "Section Title",
  "text": "<p>HTML content preserved</p>",
  "level": 1,
  "subsections": [
    {
      "title": "Subsection Title",
      "text": "<p>Subsection content</p>",
      "level": 2,
      "subsections": []
    }
  ]
}
```

### Fields

- **`title`**: Text content of the highest-level heading in the section
- **`text`**: All content except headings, with HTML formatting preserved
- **`level`**: Aria level of the main heading (1-6, or custom levels)
- **`subsections`**: Array of nested subsections with the same structure

## Examples

### Simple Section

**Input HTML:**
```html
<section>
    <h2>Getting Started</h2>
    <p>Welcome to our <a href="/api">API</a>!</p>
    <ul>
        <li>Step 1: Register</li>
        <li>Step 2: Get API key</li>
    </ul>
</section>
```

**Output:**
```json
{
  "title": "Getting Started",
  "text": "<p>Welcome to our <a href=\"/api\">API</a>!</p>\n<ul>\n<li>Step 1: Register</li>\n<li>Step 2: Get API key</li>\n</ul>",
  "level": 2,
  "subsections": []
}
```

### Nested Sections

**Input HTML:**
```html
<main>
    <h1>Documentation</h1>
    <p>Introduction text.</p>
    <h2>Installation</h2>
    <p>Installation instructions.</p>
    <h3>Requirements</h3>
    <p>System requirements.</p>
    <h2>Usage</h2>
    <p>Usage examples.</p>
</main>
```

**Output:**
```json
{
  "title": "Documentation",
  "text": "<p>Introduction text.</p>",
  "level": 1,
  "subsections": [
    {
      "title": "Installation",
      "text": "<p>Installation instructions.</p>",
      "level": 2,
      "subsections": [
        {
          "title": "Requirements",
          "text": "<p>System requirements.</p>",
          "level": 3,
          "subsections": []
        }
      ]
    },
    {
      "title": "Usage",
      "text": "<p>Usage examples.</p>",
      "level": 2,
      "subsections": []
    }
  ]
}
```

## Supported HTML Elements

### Included Elements
- Paragraphs (`<p>`)
- Lists (`<ul>`, `<ol>`, `<li>`)
- Links (`<a>`)
- Formatting (`<strong>`, `<em>`, `<code>`, etc.)
- Semantic elements (`<section>`, `<article>`, `<aside>`, etc.)
- Tables (`<table>`, `<tr>`, `<td>`, etc.)
- Media (`<img>`, `<figure>`)
- Code blocks (`<pre>`, `<code>`)
- Quotes (`<blockquote>`, `<q>`)
- All other content elements with meaningful text

### Excluded Elements
- Headings (processed separately as section titles)
- Script and style tags
- Meta elements
- Empty elements
- Elements containing headings (processed as subsections)

## Smart Root Element Detection

The tool automatically detects the best root element in this priority order:

1. `<main>` - Primary content area
2. `<article>` - Standalone article content
3. `<section>` - Document section
4. `<body>` - Document body
5. First substantial `<div>` - Fallback for div-based layouts
6. Entire document - Last resort

## Advanced Features

### Custom Headings
Supports custom headings with ARIA attributes:

```html
<div role="heading" aria-level="2">Custom Heading</div>
```

### Aria Level Overrides
Standard headings can have their levels overridden:

```html
<h3 aria-level="1">This is treated as level 1</h3>
```

### Mixed Content
Handles complex layouts with mixed content types:

```html
<div>
    <h1>Main Title</h1>
    <p>Introduction</p>
    <section>
        <h2>Section in Section</h2>
        <p>Section content</p>
    </section>
    <h2>Regular Heading</h2>
    <p>Regular content</p>
</div>
```

## Testing

Run the test suite:

```bash
python -m pytest tests/ -v
```

The project includes comprehensive tests covering:
- Basic parsing functionality
- Heading level detection
- Content extraction
- Section handling
- Edge cases and error conditions

## License

This project is open source. See LICENSE file for details.

## Contributing

Contributions are welcome! Please submit pull requests with tests for any new features.