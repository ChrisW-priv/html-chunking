#!/usr/bin/env python3
import sys
import json


def read_input(input_file: str | None = None) -> str:
    """Read JSON content from a file or stdin and parse it."""
    try:
        if input_file:
            with open(input_file, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = sys.stdin.read()
    except Exception as e:
        raise RuntimeError(f"Error reading input: {e}")

    if not content.strip():
        raise ValueError("No input JSON provided")
    return content


def write_output(output: str, output_file: str | None = None) -> None:
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        sys.stdout.write(output)


def write_stream_of_obj(obj_stream, output_file: str | None = None):
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            for obj in obj_stream:
                f.write(json.dumps(obj))
                f.write("\n")
    else:
        for obj in obj_stream:
            sys.stdout.write(json.dumps(obj))
            sys.stdout.write("\n")
