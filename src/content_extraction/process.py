import argparse
import sys
import logging

from content_extraction.logging_config import setup_logging
from content_extraction.file_handlers import process_file


logger = logging.getLogger(__name__)


def main():
    """
    Main function to process the input file/URL and generate structured output.
    """
    setup_logging()
    parser = argparse.ArgumentParser(
        description='Process various document types (PDF, PPTX, DOCX, MD, HTML, URL) and extract content into a structured HTML format.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run from the project root directory (`content-extraction/`)

  # Process a local PDF file
  python src/process.py my_document.pdf -o ./output_folder

  # Process a PowerPoint file silently
  python src/process.py my_slides.pptx --silent

  # Process a remote URL, letting the script determine the type
  python src/process.py https://example.com/document.pdf

  # Process a remote URL, forcing the type to be treated as HTML
  python src/process.py https://example.com/some-page --force-ext html
""",
    )

    parser.add_argument('input_path', help='Path to the input file or a URL to process.')
    parser.add_argument(
        '-o',
        '--output',
        default='output',
        help="Path to the output directory (defaults to 'output').",
    )
    parser.add_argument(
        '--force-ext',
        default=None,
        help="Force the handler for a specific file extension (e.g., 'pdf', 'pptx') when auto-detection is ambiguous or incorrect.",
    )

    args = parser.parse_args()

    logger.info(f'Processing file: {args.input_path}')
    process_file(args.input_path, args.output, args.force_ext)
    logger.info('Processing complete.')


if __name__ == '__main__':
    sys.exit(main())
