import os
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlparse

import requests

from content_extraction.extract_from_pptx import extract_content as extract_pptx_content

# Mapping of MIME types to file extensions
MIME_TYPE_TO_EXT = {
    'application/pdf': '.pdf',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'text/markdown': '.md',
    'text/html': '.html',
}

# Mapping of file extensions to handler functions
EXTENSION_HANDLERS = {
    '.pdf': 'handle_pdf',
    '.pptx': 'handle_pptx',
    '.docx': 'handle_docx',
    '.md': 'handle_markdown',
    '.html': 'handle_html',
}

class FileHandlerError(Exception):
    """Custom exception for file handling errors."""
    pass

def handle_pdf(file_path: str, output_dir: str):
    """
    Handles PDF files by running the main processing script.
    """
    print(f"Processing PDF file: {file_path}")
    # This path assumes the script is located at src/scripts/process_document.sh
    script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'process_document.sh')

    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Processing script not found at: {script_path}")

    # Ensure the script is executable
    if not os.access(script_path, os.X_OK):
        os.chmod(script_path, 0o755)

    try:
        result = subprocess.run(
            [script_path, file_path, output_dir],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        print(result.stdout)
        print("PDF processing completed successfully.")
        # The script should produce a final index.html in the output directory
        return os.path.join(output_dir, 'index.html')
    except subprocess.CalledProcessError as e:
        print(f"Error processing PDF file: {file_path}", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)
        raise FileHandlerError(f"PDF processing failed for {file_path}") from e

def handle_pptx(file_path: str, output_dir: str):
    """
    Handles PowerPoint files using the existing pptx extraction function.
    """
    print(f"Processing PPTX file: {file_path}")
    html_out, _ = extract_pptx_content(file_path, output_dir)
    if not html_out:
        raise FileHandlerError(f"Failed to extract content from {file_path}")
    print(f"PPTX content extracted to {html_out}")
    return html_out

def _convert_with_pandoc(file_path: str, output_dir: str, file_type: str):
    """Helper function to run pandoc for different file types."""
    print(f"Processing {file_type} file: {file_path}")
    output_html_path = os.path.join(output_dir, 'output.html')
    try:
        subprocess.run(
            ['pandoc', file_path, '-s', '-o', output_html_path], # -s for standalone
            check=True,
            capture_output=True,
            text=True
        )
        print(f"{file_type} file converted to {output_html_path}")
        return output_html_path
    except FileNotFoundError:
        error_msg = "Error: `pandoc` command not found. Please ensure pandoc is installed and in your PATH."
        print(error_msg, file=sys.stderr)
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
    Handles HTML files by copying them to the output directory.
    This can be a starting point for further HTML processing.
    """
    print(f"Processing HTML file: {file_path}")
    dest_path = os.path.join(output_dir, 'output.html')
    shutil.copy(file_path, dest_path)
    print(f"HTML file copied to {dest_path}")
    return dest_path

def handle_url(url: str, output_dir: str, force_ext: str = None):
    """
    Handles a URL by downloading the content, determining the file type,
    and passing it to the appropriate handler.
    """
    print(f"Processing URL: {url}")
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
    except requests.RequestException as e:
        raise FileHandlerError(f"Failed to download URL {url}: {e}") from e

    file_ext = None
    if force_ext:
        file_ext = f".{force_ext.lstrip('.')}"
    else:
        content_type = response.headers.get('content-type')
        if content_type:
            mime_type = content_type.split(';')[0].strip()
            file_ext = MIME_TYPE_TO_EXT.get(mime_type)

        if not file_ext:
            parsed_url = urlparse(url)
            _, file_ext_from_url = os.path.splitext(parsed_url.path)
            if file_ext_from_url:
                file_ext = file_ext_from_url

    if not file_ext or file_ext.lower() not in EXTENSION_HANDLERS:
        print(f"Could not determine file type for {url}. Defaulting to HTML.", file=sys.stderr)
        file_ext = '.html'

    handler_name = EXTENSION_HANDLERS.get(file_ext.lower())
    if not handler_name:
        raise FileHandlerError(f"No handler found for file type '{file_ext}' from URL {url}")

    handler_func = globals()[handler_name]

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext, dir=output_dir) as temp_file:
        for chunk in response.iter_content(chunk_size=8192):
            temp_file.write(chunk)
        temp_file_path = temp_file.name

    print(f"URL content saved to temporary file: {temp_file_path}")

    try:
        return handler_func(temp_file_path, output_dir)
    finally:
        os.unlink(temp_file_path)

def get_file_handler(input_path: str, force_ext: str = None):
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

    handler_name = EXTENSION_HANDLERS.get(file_ext.lower())

    if not handler_name or handler_name not in globals():
        raise ValueError(f"Unsupported file type: {file_ext}")

    # Return a lambda that captures the file path for the local file handler
    return lambda output_dir: globals()[handler_name](input_path, output_dir)
