#!/usr/bin/env python3
"""
Markdown File Formatting Automation Script

This script automates two specific formatting fixes in a Markdown file:
1. Adjusting heading levels based on numerical hierarchy.
2. Formatting the REFERENCES section with consistent spacing.

It operates as a command-line tool, reading from a file or stdin and
writing to a file or stdout, in a standard UNIX-like fashion.
"""

import re
import argparse
import sys
from content_extraction.common_std_io import read_input, write_output


def adjust_headings(lines):
    """
    Adjusts heading levels to match numerical hierarchy and separates paragraphs.

    This function yields lines of text, ensuring appropriate spacing around
    headings and their associated paragraphs.

    Args:
        lines (list): A list of strings, where each string is a line from the input.

    Yields:
        str: The processed lines of text.
    """
    HEADING_PATTERN = re.compile(r"^(#*)\s*(\d+(?:\.\d+)*)\s*(.*)$")

    for line in lines:
        match = HEADING_PATTERN.match(line)

        if not match:
            # Keep non-matching lines as is
            yield line
            continue

        # A candidate heading was found
        _, heading_number, heading_text = match.groups()

        # Determine correct markdown level
        parts = heading_number.split('.')
        desired_hashes_count = len(parts) + 1

        # Process heading text to separate title from a potential inline paragraph.
        heading_text_stripped = heading_text.strip()
        clean_title = heading_text_stripped
        paragraph = None

        if '.' in heading_text_stripped:
            title_parts = heading_text_stripped.split('.', 1)
            potential_paragraph = title_parts[1].strip()

            # If the part after the period has letters, it's a paragraph.
            if potential_paragraph and potential_paragraph[0].isalpha():
                clean_title = title_parts[0].strip() + "."
                paragraph = potential_paragraph

        # Yield a blank line before the new heading for spacing
        yield ""
        # Construct and yield the new heading line
        new_heading_line = "#" * desired_hashes_count + " " + heading_number + " " + clean_title
        yield new_heading_line

        if paragraph:
            # Yield a blank line between heading and its paragraph, then the paragraph
            yield ""
            yield paragraph


def format_references(lines):
    """
    Format the REFERENCES section with consistent spacing.

    Args:
        lines (list): List of lines from the input file.

    Returns:
        list: Modified lines with properly formatted references.
    """
    modified_lines = []
    in_references_section = False

    for line in lines:
        # Check if we're entering the REFERENCES section
        if line.strip() == "# REFERENCES":
            in_references_section = True
            modified_lines.append(line)
            continue

        if in_references_section:
            stripped = line.strip()
            if stripped:  # If the line is not empty
                modified_lines.append(stripped)
                # Append one blank line after each non-empty line
                modified_lines.append("")
        else:
            # Not in references section
            modified_lines.append(line)

    return modified_lines


def process_markdown_content(content, verbose=False):
    """
    Process markdown content with both formatting fixes.

    Args:
        content (str): The entire markdown content as a single string.
        verbose (bool): If True, print progress messages to stderr.

    Returns:
        str: The processed markdown content as a single string.
    """
    lines = content.splitlines()

    if verbose:
        print(f"Processing {len(lines)} lines...", file=sys.stderr)

    # Part 1: Adjust heading levels
    if verbose:
        print("Part 1: Adjusting heading levels...", file=sys.stderr)
    adjusted_lines_generator = adjust_headings(lines)

    # Part 2: Format references section
    if verbose:
        print("Part 2: Formatting references section...", file=sys.stderr)
    # Consume the generator to pass a list to the next function
    formatted_lines = format_references(list(adjusted_lines_generator))

    # Join lines back into a single string with a trailing newline
    return '\n'.join(formatted_lines) + '\n'


def main():
    """Main function to handle command line arguments and execute the script."""
    parser = argparse.ArgumentParser(
        description="Automate markdown file formatting fixes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.md                    # Parse file, output to stdout
  %(prog)s -o output.md input.md     # Parse file, save to file
  cat input.md | %(prog)s              # Parse from stdin
  %(prog)s --verbose input.md          # Show debug information
        """
    )
    parser.add_argument(
        "input_file",
        nargs='?',
        help="Path to input markdown file (if not provided, reads from stdin)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Path to output markdown file (if not provided, writes to stdout)"
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show verbose output and debug information'
    )
    args = parser.parse_args()

    try:
        # Read input from file or stdin
        if args.verbose:
            source = args.input_file or "stdin"
            print(f"Reading from: {source}", file=sys.stderr)

        markdown_content = read_input(args.input_file)

        # Process the markdown content
        processed_content = process_markdown_content(markdown_content, args.verbose)

        # Write output to file or stdout
        write_output(processed_content, args.output)

        if args.verbose:
            destination = args.output or "stdout"
            print(f"Processing complete. Output written to: {destination}", file=sys.stderr)

        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
