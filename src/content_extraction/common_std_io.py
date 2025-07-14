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


def write_output(
    nodes: list[dict[str, object]], output_file: str | None = None
) -> None:
    """Write the list of node dicts as JSON Lines to a file or stdout."""
    try:
        out_stream = open(output_file, 'w', encoding='utf-8') if output_file else sys.stdout
        for node in nodes:
            out_stream.write(json.dumps(node, ensure_ascii=False))
            out_stream.write("\n")
    except Exception as e:
        raise RuntimeError(f"Error writing output: {e}")
    finally:
        if output_file:
            out_stream.close()
