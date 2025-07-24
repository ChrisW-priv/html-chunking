import argparse
import os
import sys

# This allows the script to be run from the project root, e.g. `python src/process.py ...`
# It adds the `src` directory to the Python path.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


from content_extraction.file_handlers import get_file_handler, FileHandlerError

def main():
    """
    Main function to process the input file/URL and generate structured output.
    """
    parser = argparse.ArgumentParser(
        description="Process various document types (PDF, PPTX, DOCX, MD, HTML, URL) and extract content into a structured HTML format.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run from the project root directory (`content-extraction/`)

  # Process a local PDF file
  python src/process.py my_document.pdf -o ./output_folder

  # Process a PowerPoint file
  python src/process.py my_slides.pptx

  # Process a remote URL, letting the script determine the type
  python src/process.py https://example.com/document.pdf

  # Process a remote URL, forcing the type to be treated as HTML
  python src/process.py https://example.com/some-page --force-ext html
"""
    )

    parser.add_argument(
        "input_path",
        help="Path to the input file or a URL to process."
    )
    parser.add_argument(
        "-o", "--output",
        default="output",
        help="Path to the output directory (defaults to 'output')."
    )
    parser.add_argument(
        "--force-ext",
        default=None,
        help="Force the handler for a specific file extension (e.g., 'pdf', 'pptx') when auto-detection is ambiguous or incorrect."
    )

    args = parser.parse_args()

    # Ensure the output directory exists
    try:
        os.makedirs(args.output, exist_ok=True)
    except OSError as e:
        print(f"Error: Could not create output directory at '{args.output}'. Details: {e}", file=sys.stderr)
        return 1

    try:
        # Get the appropriate handler based on the input path and force_ext flag
        print(f"Attempting to process '{args.input_path}'...")
        handler = get_file_handler(args.input_path, args.force_ext)

        # Execute the handler, which will perform the full processing pipeline
        final_html_path = handler(args.output)

        if final_html_path and os.path.exists(final_html_path):
            print(f"\nProcessing complete!")
            print(f"Final structured HTML output is available at: {final_html_path}")
            return 0
        else:
            print(f"Processing finished, but the final output file '{final_html_path}' was not found.", file=sys.stderr)
            return 1

    except (FileNotFoundError, ValueError, FileHandlerError) as e:
        print(f"\nAn error occurred during processing: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
