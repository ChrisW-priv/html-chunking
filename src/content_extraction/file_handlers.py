import os
import shutil
import subprocess
import sys
import tempfile
import mimetypes
from urllib.parse import urlparse

import requests

from content_extraction.extract_from_pptx import extract_content as extract_pptx_content
from content_extraction.semantic_chunk_html import HTMLSectionParser
from content_extraction.common_std_io import write_stream_of_obj
from content_extraction.split_and_create_digest import process_node


class FileHandlerError(Exception):
    """Custom exception for file handling errors."""


def _convert_with_pandoc(file_path: str, output_dir: str):
    """Helper function to run pandoc for different file types."""
    output_html_path = os.path.join(output_dir, "index.html")
    try:
        subprocess.run(
            ["pandoc", file_path, "-s", "-o", output_html_path],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return output_html_path
    except FileNotFoundError:
        error_msg = "Error: `pandoc` command not found. Please ensure pandoc is installed and in your PATH."
        raise FileHandlerError(error_msg)
    except subprocess.CalledProcessError as e:
        print(f"Error converting {file_path} to HTML: {e.stderr}", file=sys.stderr)
        raise FileHandlerError(f"Pandoc conversion failed for {file_path}") from e


def handle_pdf(file_path: str, output_dir: str):
    """
    Handles PDF files by running the main processing script.
    The script is expected to convert the PDF to HTML and place it as index.html
    in the output_dir.
    """
    print(f"Processing PDF file: {file_path}")
    # This path assumes the script is located at src/scripts/process_document.sh
    script_path = os.path.join(
        os.path.dirname(__file__), "..", "scripts", "process_document.sh"
    )
    output_html_path = os.path.join(output_dir, "index.html")  # Define output_html_path

    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Processing script not found at: {script_path}")

    # Ensure the script is executable
    if not os.access(script_path, os.X_OK):
        print(
            f"Warning: Script {script_path} is not executable. Attempting to set permissions.",
            file=sys.stderr,
        )
        try:
            os.chmod(script_path, 0o755)
        except OSError as e:
            raise FileHandlerError(
                f"Failed to set executable permissions for {script_path}: {e}"
            )

    try:
        # The script is expected to take input_file and output_directory as arguments
        subprocess.run(
            [script_path, file_path, output_dir],
            check=True,  # Raise CalledProcessError if the command returns a non-zero exit code
            capture_output=True,  # Capture stdout and stderr
            text=True,  # Decode stdout/stderr as text
            encoding="utf-8",
        )
        if not os.path.exists(output_html_path):
            raise FileHandlerError(
                f"Processing script {script_path} completed, but did not produce the expected output file: {output_html_path}"
            )

        return output_html_path
    except subprocess.CalledProcessError as e:
        print(f"Error processing PDF with script: {e.stderr}", file=sys.stderr)
        raise FileHandlerError(f"PDF processing script failed for {file_path}") from e


def handle_pptx(file_path: str, output_dir: str):
    """
    Handles PowerPoint files using the existing pptx extraction function.
    """
    html_out, _ = extract_pptx_content(file_path, output_dir)
    if not html_out:
        raise FileHandlerError(f"Failed to extract content from {file_path}")

    # Standardize the output filename to index.html
    standard_path = os.path.join(output_dir, "index.html")
    if os.path.abspath(html_out) != os.path.abspath(standard_path):
        shutil.move(html_out, standard_path)
    return standard_path


def handle_docx(file_path: str, output_dir: str):
    """Handles Word documents by converting them to HTML using pandoc."""
    return _convert_with_pandoc(file_path, output_dir)


def handle_markdown(file_path: str, output_dir: str):
    """Handles Markdown files by converting them to HTML using pandoc."""
    return _convert_with_pandoc(file_path, output_dir)


def handle_html(file_path: str, output_dir: str):
    """
    Handles HTML files by copying them to the output directory with the standard name.
    """
    dest_path = os.path.join(output_dir, "index.html")
    if os.path.abspath(file_path) != os.path.abspath(dest_path):
        shutil.move(file_path, dest_path)
    return dest_path


def handle_url(url: str, output_dir: str, force_ext: str = ""):
    """
    Handles a URL by determining the file type and using the most efficient
    processing method.
    """
    file_ext = None

    if force_ext:
        file_ext = f".{force_ext.lstrip('.')}"
    else:
        try:
            response = requests.head(url, timeout=15, allow_redirects=True)
            response.raise_for_status()
            content_type = response.headers.get("content-type")
            if content_type:
                mime_type = content_type.split(";")[0].strip()
                file_ext = mimetypes.guess_extension(mime_type)

            if not file_ext or file_ext in [".bin"]:
                parsed_url = urlparse(url)
                _, ext_from_url = os.path.splitext(parsed_url.path)
                if ext_from_url:
                    file_ext = ext_from_url

        except requests.RequestException as e:
            raise FileHandlerError(
                f"Failed to retrieve headers from URL {url}: {e}"
            ) from e

    if not file_ext or file_ext.lower() not in EXTENSION_HANDLERS:
        print(
            f"Could not determine a supported file type for {url}. Defaulting to HTML.",
            file=sys.stderr,
        )
        file_ext = ".html"

    # Download to a temporary file for all types except HTML, which is streamed.
    if file_ext == ".html":
        output_html_path = os.path.join(output_dir, "index.html")
        try:
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(output_html_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return output_html_path
        except requests.RequestException as e:
            raise FileHandlerError(f"Failed to download HTML content from {url}: {e}")

    handler_func = EXTENSION_HANDLERS.get(file_ext.lower())
    if not handler_func:
        raise FileHandlerError(
            f"No handler found for file type '{file_ext}' from URL {url}"
        )

    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file_path = temp_file.name

        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(temp_file_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        return handler_func(temp_file_path, output_dir)

    except requests.RequestException as e:
        raise FileHandlerError(f"Failed to download content from {url}: {e}") from e
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


# Mapping of file extensions to handler functions
EXTENSION_HANDLERS = {
    ".pdf": handle_pdf,
    ".pptx": handle_pptx,
    ".docx": handle_docx,
    ".md": handle_markdown,
    ".html": handle_html,
}


def get_handler(input_path: str, force_ext: str = ""):
    """
    Determines and returns the correct file handler function based on the input.
    """
    if input_path.startswith(("http://", "https://")):
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

    return lambda output_dir: handler_func(input_path, output_dir)


def process_file(input_path: str, output_dir: str, force_ext: str = "") -> str:
    """
    Main entry point for processing a file or URL.
    It identifies the file type, runs the appropriate handler, and returns the path to the final processed HTML file.
    """
    os.makedirs(output_dir, exist_ok=True)
    handler = get_handler(input_path, force_ext)
    final_html_path = handler(output_dir)

    if not final_html_path or not os.path.exists(final_html_path):
        raise FileHandlerError(
            f"Processing failed to produce an output file for '{input_path}'"
        )

    print("Parsing HTML into sections...")
    try:
        with open(final_html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    except Exception as e:
        raise FileHandlerError(
            f"Failed to read the generated HTML file at {final_html_path}: {e}"
        )

    parser = HTMLSectionParser()
    parsed_sections = parser.parse_sections(html_content)

    print("Splitting parsed sections and creating JSON digest...")
    jsonl_output_path = os.path.join(output_dir, "sections.jsonl")

    all_nodes = []
    if parsed_sections:
        for section in parsed_sections:
            all_nodes.extend(process_node(section, parent_digest_hash=None))

    write_stream_of_obj(all_nodes, jsonl_output_path)
    print(f"Successfully created JSON digest at {jsonl_output_path}")

    return final_html_path
