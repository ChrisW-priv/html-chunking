import os
import shutil
import subprocess
import sys
import tempfile
import mimetypes
from urllib.parse import urlparse

import requests

from content_extraction.extract_from_pptx import extract_content as extract_pptx_content


class FileHandlerError(Exception):
    """Custom exception for file handling errors."""


def handle_pdf(file_path: str, output_dir: str):
    """
    Handles PDF files (local or URL) by running the main processing script.
    """
    # Correct path to the script from this file's location
    script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'process_document.sh')

    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Processing script not found at: {script_path}")

    if not os.access(script_path, os.X_OK):
        os.chmod(script_path, 0o755)

    try:
        # The script is designed to take a file path or URL and an output directory
        subprocess.run(
            [script_path, file_path, output_dir],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        # The script is expected to create index.html in the output directory
        return os.path.join(output_dir, 'index.html')
    except subprocess.CalledProcessError as e:
        print(f"Error processing PDF file/url: {file_path}", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)
        raise FileHandlerError(f"PDF processing failed for {file_path}") from e


def handle_pptx(file_path: str, output_dir: str):
    """
    Handles PowerPoint files using the existing pptx extraction function.
    """
    # The pptx extractor outputs to 'output.html' by default
    html_out, _ = extract_pptx_content(file_path, output_dir)
    if not html_out:
        raise FileHandlerError(f"Failed to extract content from {file_path}")

    return html_out


def _convert_with_pandoc(file_path: str, output_dir: str, file_type: str):
    """Helper function to run pandoc for different file types."""
    # Standardize output file name
    output_html_path = os.path.join(output_dir, 'index.html')
    try:
        subprocess.run(
            ['pandoc', file_path, '-s', '-o', output_html_path],  # -s for standalone
            check=True,
            capture_output=True,
            text=True
        )
        return output_html_path
    except FileNotFoundError:
        error_msg = "Error: `pandoc` command not found. Please ensure pandoc is installed and in your PATH."
        raise FileHandlerError(error_msg)
    except subprocess.CalledProcessError as e:
        print(f"Error converting {file_type} to HTML: {e.stderr}", file=sys.stderr)
        raise FileHandlerError(f"Pandoc conversion failed for {file_path}") from e


def handle_docx(file_path: str, output_dir: str):
    """Handles Word documents by converting them to HTML using pandoc."""
    return _convert_with_pandoc(file_path, output_dir, "DOCX")


def handle_markdown(file_path: str, output_dir: str):
    """Handles Markdown files by converting them to HTML using pandoc."""
    return _convert_with_pandoc(file_path, output_dir, "Markdown")


def handle_html(file_path: str, output_dir: str):
    """
    Handles HTML files by copying them to the output directory with the standard name.
    """
    dest_path = os.path.join(output_dir, 'index.html')
    # Use copy to avoid moving the original file if it's a local source
    shutil.move(file_path, dest_path)
    return dest_path


def handle_url(url: str, output_dir: str, force_ext: str = ""):
    """
    Handles a URL by determining the file type and using the most efficient
    processing method.
    """
    file_ext = None

    # 1. Determine the file extension
    if force_ext:
        file_ext = f".{force_ext.lstrip('.')}"
    else:
        try:
            # Use a HEAD request to be efficient
            response = requests.head(url, timeout=15, allow_redirects=True)
            response.raise_for_status()
            content_type = response.headers.get('content-type')
            if content_type:
                # Guess extension from MIME type
                mime_type = content_type.split(';')[0].strip()
                file_ext = mimetypes.guess_extension(mime_type)

            # Fallback to URL path if MIME type is not helpful
            if not file_ext or file_ext == '.bin':
                parsed_url = urlparse(url)
                _, ext_from_url = os.path.splitext(parsed_url.path)
                if ext_from_url:
                    file_ext = ext_from_url

        except requests.RequestException as e:
            raise FileHandlerError(f"Failed to retrieve headers from URL {url}: {e}") from e

    # Default to HTML if we can't figure it out
    if not file_ext or file_ext.lower() not in EXTENSION_HANDLERS:
        print(f"Could not determine a specific file type for {url}. Defaulting to HTML.", file=sys.stderr)
        file_ext = '.html'

    # 2. Process based on determined extension

    # PDF: Don't download, the handler can take a URL directly.
    if file_ext == '.pdf':
        return handle_pdf(url, output_dir)

    # HTML: Stream directly to the final destination file.
    if file_ext == '.html':
        output_html_path = os.path.join(output_dir, 'index.html')
        try:
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(output_html_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=4096):
                        f.write(chunk)
            return output_html_path
        except requests.RequestException as e:
            raise FileHandlerError(f"Failed to download HTML content from {url}: {e}")

    # Other types (PPTX, DOCX, MD): Download to a temporary file for processing.
    handler_func = EXTENSION_HANDLERS.get(file_ext.lower())
    if not handler_func:
        raise FileHandlerError(f"No handler found for file type '{file_ext}' from URL {url}")

    temp_file_path = None
    try:
        # Create a temporary file to hold the downloaded content
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file_path = temp_file.name

            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=4096):
                    temp_file.write(chunk)
            # Process the temporary file
            return handler_func(temp_file_path, output_dir)

    except requests.RequestException as e:
        raise FileHandlerError(f"Failed to download content from {url}: {e}") from e
    finally:
        # Ensure the temporary file is deleted
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


# Mapping of file extensions to handler functions
EXTENSION_HANDLERS = {
    '.pdf': handle_pdf,
    '.pptx': handle_pptx,
    '.docx': handle_docx,
    '.md': handle_markdown,
    '.html': handle_html,
}


def get_handler(input_path: str, force_ext: str = None):
    """
    Determines and returns the correct file handler function based on the input.
    """
    if input_path.startswith(('http://', 'https://')):
        # Return a lambda that captures the arguments for the URL handler
        return lambda output_dir: handle_url(input_path, output_dir, force_ext)

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    _, ext = os.path.splitext(input_path)
    file_ext = f".{force_ext.lstrip('.')}" if force_ext else ext

    if not file_ext:
        raise ValueError("File has no extension, and --force-ext was not provided.")

    handler_func = EXTENSION_HANDLERS.get(file_ext.lower())

    if not handler_func:
        raise ValueError(f"Unsupported file type: {file_ext}")

    # Return a lambda that captures the file path for the local file handler
    return lambda output_dir: handler_func(input_path, output_dir)


def process_file(input_path: str, output_dir: str, force_ext: str = None) -> str:
    """
    Main entry point for processing a file or URL.
    It identifies the file type, runs the appropriate handler, and returns the path to the final processed HTML file.
    """
    os.makedirs(output_dir, exist_ok=True)
    handler = get_handler(input_path, force_ext)
    final_html_path = handler(output_dir)
    if not final_html_path or not os.path.exists(final_html_path):
        raise FileHandlerError(f"Processing failed to produce an output file for '{input_path}'")
    return final_html_path
