#!/usr/bin/env python3
"""
HTML Content Extraction CLI

A command-line tool for extracting structured content from HTML documents.
Converts HTML sections into hierarchical JSON data with preserved formatting.

Usage:
    python main.py [options] [input_file]

Examples:
    # Read from stdin, output to stdout
    cat example.html | python main.py

    # Read from file, output to stdout
    python main.py input.html

    # Read from stdin, output to file
    python main.py -o output.json

    # Read from file, output to file
    python main.py input.html -o output.json

    # Pretty print JSON output
    python main.py --pretty input.html

    # Verbose mode with debug information
    python main.py --verbose input.html
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup


from src.content_extraction import SectionParser


def read_input(input_file: Optional[str] = None) -> str:
    """Read HTML content from file or stdin."""
    try:
        if input_file:
            if not Path(input_file).exists():
                raise FileNotFoundError(f"Input file not found: {input_file}")

            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if not content.strip():
                raise ValueError(f"Input file is empty: {input_file}")

        else:
            # Read from stdin
            content = sys.stdin.read()

            if not content.strip():
                raise ValueError("No input provided via stdin")

        return content

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        sys.exit(1)


def write_output(data: Dict[str, Any], output_file: Optional[str] = None, pretty: bool = False) -> None:
    """Write JSON data to file or stdout."""
    try:
        if pretty:
            json_output = json.dumps(data, indent=2, ensure_ascii=False)
        else:
            json_output = json.dumps(data, ensure_ascii=False)

        if output_file:
            # Ensure output directory exists
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_output)
                f.write('\n')  # Add newline at end

            print(f"Output written to: {output_file}", file=sys.stderr)
        else:
            # Write to stdout
            print(json_output)

    except Exception as e:
        print(f"Error writing output: {e}", file=sys.stderr)
        sys.exit(1)



def parse_html(html_content: str, verbose: bool = False) -> Dict[str, Any]:
    """Parse HTML content and extract structured data."""
    try:
        if verbose:
            print(f"Parsing HTML content ({len(html_content)} characters)...", file=sys.stderr)

        # Extract structured content
        parser = SectionParser()
        result = parser.parse_html(html_content)

        if verbose:
            print(f"Extracted {len(result.get('subsections', []))} subsections", file=sys.stderr)

        return result

    except Exception as e:
        print(f"Error parsing HTML: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Extract structured content from HTML documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.html                    # Parse file, output to stdout
  %(prog)s -o output.json input.html     # Parse file, save to JSON
  cat input.html | %(prog)s              # Parse from stdin
  %(prog)s --pretty input.html           # Pretty-printed JSON output
  %(prog)s --verbose input.html          # Show debug information
        """
    )

    parser.add_argument(
        'input_file',
        nargs='?',
        help='Input HTML file (if not provided, reads from stdin)'
    )

    parser.add_argument(
        '-o', '--output',
        metavar='FILE',
        help='Output JSON file (if not provided, writes to stdout)'
    )

    parser.add_argument(
        '--pretty',
        action='store_true',
        help='Pretty-print JSON output with indentation'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show verbose output and debug information'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )

    args = parser.parse_args()

    try:
        # Read input
        if args.verbose:
            if args.input_file:
                print(f"Reading from file: {args.input_file}", file=sys.stderr)
            else:
                print("Reading from stdin...", file=sys.stderr)

        html_content = read_input(args.input_file)

        # Parse HTML
        result = parse_html(html_content, args.verbose)

        # Write output
        write_output(result, args.output, args.pretty)

        if args.verbose:
            print("Processing completed successfully", file=sys.stderr)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
