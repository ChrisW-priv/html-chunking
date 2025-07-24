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
import difflib
from typing import Iterable
import sys

from content_extraction.common_std_io import write_output


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
    HEADING_PATTERN = re.compile(
        r"^(#*)\s+([A-Z]\s?(?:\.\s*\d+)*|\d+(?:\.\s*\d+)*)\s*(.*)$"
    )
    ORDERED_LIST_PATTERN = re.compile(r"^\s*\d+\.\s")

    for line in lines:
        # If the line is a numbered list item, leave it as is.
        if ORDERED_LIST_PATTERN.match(line):
            yield line
            continue

        match = HEADING_PATTERN.match(line)

        if not match:
            stripped_line = line.lstrip()
            if stripped_line.startswith("#"):
                # Default non-matching headings to level 4
                text = stripped_line.lstrip("#").strip()
                yield ""
                yield "#### " + text
                continue

            # Keep non-matching lines as is
            yield line
            continue

        # A candidate heading was found
        _, heading_number, heading_text = match.groups()

        # Determine correct markdown level
        parts = heading_number.split(".")
        desired_hashes_count = len(parts) + 1

        # Process heading text to separate title from a potential inline paragraph.
        heading_text_stripped = heading_text.strip()
        clean_title = heading_text_stripped
        paragraph = None

        if "." in heading_text_stripped:
            title_parts = heading_text_stripped.split(".", 1)
            potential_paragraph = title_parts[1].strip()

            # If the part after the period has letters, it's a paragraph.
            if potential_paragraph and potential_paragraph[0].isalpha():
                clean_title = title_parts[0].strip() + "."
                paragraph = potential_paragraph

        # Yield a blank line before the new heading for spacing
        yield ""
        # Construct and yield the new heading line
        new_heading_line = (
            "#" * desired_hashes_count + " " + heading_number + " " + clean_title
        )
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


def process_science_paper(text_file_content: str, heading_file_content: str):
    """
    Process markdown content with both formatting fixes.

    """
    lines = text_file_content.splitlines()

    adjusted_lines_generator = adjust_headings(lines)

    # Consume the generator to pass a list to the next function
    formatted_lines = format_references(list(adjusted_lines_generator))

    # Join lines back into a single string with a trailing newline
    return "\n".join(formatted_lines) + "\n"


def parse_ndiff(diff_lines: Iterable[str]) -> list[tuple[str, str]]:
    """
    Turn an ndiff iterable into a list of (old_line, new_line) patches.

    Only pairs up “- old” followed by “+ new” within the same hunk.
    """
    patches: list[tuple[str, str]] = []
    pending_old = None

    for line in diff_lines:
        if line.startswith("- "):
            pending_old = line[2:]
        elif line.startswith("+ ") and pending_old is not None:
            patches.append((pending_old, line[2:]))
            pending_old = None
        elif line.startswith("  ") or not line:
            patches.append((pending_old or "", ""))
            pending_old = None

    return patches


def apply_heading_patches(ocr_text: str, diff_lines: Iterable[str]) -> str:
    """
    Apply heading corrections from an ndiff iterable to the OCR text.

    For each (old, new) patch, replace the first exact match of old in the OCR
    text with new.
    """
    patches = parse_ndiff(diff_lines)
    lines = ocr_text.splitlines()

    for old_heading, new_heading in patches:
        for idx, line in enumerate(lines):
            if line == old_heading:
                lines[idx] = new_heading
                break

    return "\n".join(lines)


def process_general_paper(text_file_content: str, heading_file_content: str) -> str:
    from content_extraction.dspy_modules import CorrectHeadingLevel

    heading_corrector = CorrectHeadingLevel()
    pred = heading_corrector(heading_file_content)
    corrected_headings = pred.corrected_headings
    with open("corrected_headings.txt", "w") as f:
        f.write(corrected_headings)
    diff = difflib.ndiff(
        heading_file_content.splitlines(), corrected_headings.splitlines()
    )
    fixed_text = apply_heading_patches(text_file_content, diff)
    return fixed_text


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
        """,
    )
    parser.add_argument("ocr_input_file", help="Path to input markdown file")
    parser.add_argument(
        "headings_input_file", help="Path to markdown file with headings"
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Path to output markdown file (if not provided, writes to stdout)",
    )
    parser.add_argument(
        "--science_paper",
        action="store_true",
        help="Indicates that the input is a science paper. Parsing optimized for scientific papers.",
    )
    args = parser.parse_args()

    with open(args.ocr_input_file, "r") as f:
        markdown_content = f.read()

    with open(args.headings_input_file, "r") as f:
        headings_content = f.read()

    # Process the markdown content
    if args.science_paper:
        processed_content = process_science_paper(markdown_content, headings_content)
    else:
        processed_content = process_general_paper(markdown_content, headings_content)

    # Write output to file or stdout
    write_output(processed_content, args.output)


if __name__ == "__main__":
    sys.exit(main())
