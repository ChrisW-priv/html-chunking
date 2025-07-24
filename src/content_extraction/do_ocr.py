import os
import sys
import json
import logging
import subprocess
import base64
import requests
import argparse
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def set_env_vars():
    x = {
        "MODEL_ID": "mistral-ocr-2505",
        "PROJECT_ID": "edu-course-companion",
        "REGION": "europe-west4",
    }
    for k, v in x.items():
        os.environ[k] = v


def authenticate_and_get_token() -> str | None:
    process = subprocess.Popen(
        "gcloud auth print-access-token", stdout=subprocess.PIPE, shell=True
    )
    (access_token_bytes, err) = process.communicate()
    if err:
        logger.error(f"Error getting access token: {err.decode('utf-8')}")
        return None
    access_token = access_token_bytes.decode("utf-8").strip()
    return access_token


def build_url_to_model():
    region = os.getenv("REGION")
    project_id = os.getenv("PROJECT_ID")
    model_id = os.getenv("MODEL_ID")

    url = f"https://{region}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{region}/publishers/mistralai/models/{model_id}:rawPredict"
    return url


def file_to_base64_string(file_object):
    """
    Converts a Python file-like object to a base64 encoded string.

    Args:
        file_object: A file-like object opened in binary read mode (e.g., 'rb').

    Returns:
        A string containing the base64 encoded content of the file.
    """
    encoded_bytes = base64.b64encode(file_object.read())
    encoded_string = encoded_bytes.decode("utf-8")
    return encoded_string


def build_data_url_from_file(filepath):
    """Creates a data URL from a local file path."""
    with open(filepath, "rb") as file:
        base64_pdf = file_to_base64_string(file)
    # The API expects this specific format for data URLs
    document_url = f"data:application/pdf;base64,{base64_pdf}"
    return document_url


def build_payload(document_url):
    model_id = os.getenv("MODEL_ID")
    payload = {
        "model": model_id,
        "document": {
            "type": "document_url",
            "document_url": document_url,
        },
        "include_image_base64": True,  # Request image content
    }
    return payload


def make_request(payload) -> dict | None:
    access_token = authenticate_and_get_token()
    if access_token is None:
        return None
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    url = build_url_to_model()

    response = requests.post(url=url, headers=headers, json=payload)
    if response.status_code == 200:
        try:
            response_dict = response.json()
        except json.JSONDecodeError as e:
            logger.error("Error decoding JSON:", e)
            logger.error("Raw response:", response.text)
            return None
    else:
        logger.error(f"Request failed with status code: {response.status_code}")
        logger.error(f"Response: {response.text}")
        return None
    return response_dict


def save_response_to_disk(response_dict, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for page in response_dict.get("pages", []):
        zfilled_index = str(page["index"]).zfill(4)
        page_filename = os.path.join(output_dir, f"page-{zfilled_index}.md")
        with open(page_filename, "w", encoding="utf-8") as f:
            f.write(page["markdown"])
        for image in page.get("images", []):
            image_base64 = image["image_base64"]
            colon_index = image_base64.find(",")
            if colon_index == -1:
                logger.warning(
                    f"Could not find comma in image_base64 for {image['id']}, skipping."
                )
                continue
            encoded_image = image_base64[colon_index + 1 :]
            image_bytes = base64.b64decode(encoded_image)
            # image id already has the extension
            image_filename = os.path.join(output_dir, image["id"])
            with open(image_filename, "wb") as f:
                f.write(image_bytes)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Extract text and images from a document using OCR.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input_source", help="Input file path or URL to a document.")
    parser.add_argument(
        "-o",
        "--output",
        metavar="DIRECTORY",
        help="Output directory to save pages and images. Defaults to a directory named after the input file.",
    )
    args = parser.parse_args()

    set_env_vars()

    input_source = args.input_source
    output_dir = args.output

    # Determine default output directory if not provided
    if not output_dir:
        if input_source.startswith(("http://", "https://")):
            parsed_url = urlparse(input_source)
            filename = os.path.basename(parsed_url.path)
            output_dir = os.path.splitext(filename)[0] if filename else "ocr_output"
        else:
            output_dir = os.path.splitext(os.path.basename(input_source))[0]

    logger.info(f"Processing: {input_source}")
    logger.info(f"Output will be saved to: {output_dir}")

    try:
        if input_source.startswith(("http://", "https://")):
            # If the input is a URL, pass it directly.
            document_url = input_source
        else:
            # If the input is a local file, check for existence and create a data URL.
            if not os.path.exists(input_source):
                logger.error(f"Error: Input file not found at '{input_source}'")
                return 1
            document_url = build_data_url_from_file(input_source)

        payload = build_payload(document_url)
        response_dict = make_request(payload)

        if not response_dict:
            logger.error("Failed to get a valid response from the OCR service.")
            return 1

        save_response_to_disk(response_dict, output_dir)
        logger.info("Processing completed successfully.")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
