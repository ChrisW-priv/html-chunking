#!/usr/bin/env python3
"""
Markdown File Formatting Automation Script

This script automates two specific formatting fixes in a Markdown file:
1. Adjusting heading levels based on numerical hierarchy
2. Formatting references section with consistent spacing

Author: Assistant
"""

import re
import argparse
import sys
from pathlib import Path


def adjust_headings(lines):
    """
    Adjust heading levels to match numerical hierarchy.

    Args:
        lines (list): List of lines from the input file

    Returns:
        list: Modified lines with corrected heading levels
    """
    # Regular expression for heading candidates
    # Regular expression for heading candidates
    # It now allows for an optional '#' prefix (#*), followed by a numerical section
    # and then the heading text. The numerical section is captured in group 2.
    # The remaining text is captured in group 3.
    HEADING_PATTERN = re.compile(r"^(#*)\s*(\d+(?:\.\d+)*)\s*(.*)$")

    modified_lines = []

    for line in lines:
        match = HEADING_PATTERN.match(line)

        if not match:
            # Keep non-matching lines as is
            modified_lines.append(line.rstrip())  # Remove trailing whitespace
            continue

        # Else: a candidate heading was found
        _, heading_number, heading_text = match.groups()

        # Determine correct markdown level
        parts = heading_number.split('.')
        desired_hashes_count = len(parts) + 1

        # Process heading text to separate title from potential inline paragraph.
        # A period is used as the delimiter.
        heading_text_stripped = heading_text.strip()
        clean_title = heading_text_stripped
        paragraph = ""

        if '.' in heading_text_stripped:
            title_parts = heading_text_stripped.split('.', 1)
            potential_paragraph = title_parts[1].strip()

            # If the part after the period has letters, it's a paragraph.
            # Otherwise, it is part of the title (e.g., version "2.0").
            if potential_paragraph and potential_paragraph[0].isalpha():
                clean_title = title_parts[0].strip() + "."
                paragraph = potential_paragraph

        # Construct new heading line
        new_line = "#" * desired_hashes_count + " " + heading_number + " " + clean_title
        modified_lines.append(new_line)

        if paragraph:
            modified_lines.append(paragraph)

    return modified_lines


def format_references(lines):
    """
    Format the REFERENCES section with consistent spacing.

    Args:
        lines (list): List of lines from the input file

    Returns:
        list: Modified lines with properly formatted references
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
            if (stripped := line.strip()): # If the line is not empty
                modified_lines.append(stripped)
                # Append one blank line after each non-empty line in the references section
                modified_lines.append("")
        else:
            # Not in references section
            modified_lines.append(line)

    return modified_lines


def process_markdown_file(input_file_path, output_file_path):
    """
    Process a markdown file with both formatting fixes.

    Args:
        input_file_path (str): Path to input markdown file
        output_file_path (str): Path to output markdown file
    """
    try:
        # Read the input file
        with open(input_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Strip newlines for processing, we'll add them back when writing
        lines = [line.rstrip('\n\r') for line in lines]

        # Part 1: Adjust heading levels
        print(f"Processing {len(lines)} lines...")
        print("Part 1: Adjusting heading levels...")
        adjusted_lines = adjust_headings(lines)

        # Part 2: Format references section
        print("Part 2: Formatting references section...")
        formatted_lines = format_references(adjusted_lines)

        # Write the output file
        with open(output_file_path, 'w', encoding='utf-8') as f:
            for line in formatted_lines:
                f.write(line + '\n')

        print(f"Successfully processed file. Output written to: {output_file_path}")

    except FileNotFoundError:
        print(f"Error: Input file '{input_file_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(1)


def main():
    """Main function to handle command line arguments and execute the script."""
    parser = argparse.ArgumentParser(
        description="Automate markdown file formatting fixes"
    )
    parser.add_argument(
        "input_file",
        nargs='?',
        help="Path to input markdown file"
    )
    parser.add_argument(
        "-o", "--output",
        help="Path to output markdown file (default: input_file with '_formatted' suffix)"
    )

    args = parser.parse_args()

    # Require input file if not creating test
    if not args.input_file:
        parser.print_help()
        print("\nError: input_file is required unless using --create-test")
        sys.exit(1)

    # Handle output file path
    if not args.output:
        input_path = Path(args.input_file)
        output_path = input_path.parent / f"{input_path.stem}_formatted{input_path.suffix}"
        args.output = str(output_path)

    # Validate input file exists
    if not Path(args.input_file).exists():
        print(f"Error: Input file '{args.input_file}' does not exist.")
        sys.exit(1)

    # Process the file
    process_markdown_file(args.input_file, args.output)


if __name__ == "__main__":
    main()
