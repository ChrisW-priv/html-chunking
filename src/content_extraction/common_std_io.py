#!/usr/bin/env python3
import sys
import json


def read_input(input_file: str | None = None) -> str:
    """Read JSON content from a file or stdin and parse it."""
    try:
        if input_file:
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = sys.stdin.read()
    except Exception as e:
        raise RuntimeError(f"Error reading input: {e}")

    if not content.strip():
        raise ValueError("No input JSON provided")
    return content


def write_output( output: str, output_file: str | None = None ) -> None:
    try:
        out_stream = open(output_file, 'w', encoding='utf-8') if output_file else sys.stdout
        out_stream.write(output)
    except Exception as e:
        raise RuntimeError(f"Error writing output: {e}")
    finally:
        if output_file:
            out_stream.close()


def write_stream_of_obj(obj_stream, output_file: str | None = None):
    try:
        out_stream = open(output_file, 'w', encoding='utf-8') if output_file else sys.stdout
        for obj in obj_stream:
            out_stream.write(json.dumps(obj))
            out_stream.write('\n')
    except Exception as e:
        raise RuntimeError(f"Error writing output: {e}")
    finally:
        if output_file:
            out_stream.close()
