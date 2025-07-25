#!/usr/bin/env python3
import sys
import json
import logging
from typing import Iterable

logger = logging.getLogger(__name__)


def read_input(input_file: str | None = None) -> str:
    """Read JSON content from a file or stdin and parse it."""
    try:
        if input_file:
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = sys.stdin.read()
    except Exception as e:
        logger.error(f'Error reading input from {input_file or "stdin"}', exc_info=True)
        raise RuntimeError(f'Error reading input: {e}')

    return content


def write_output(output: str, output_file: str | None = None):
    try:
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output)
        else:
            sys.stdout.write(output)
    except IOError:
        logger.error(f'Error writing to {output_file or "stdout"}', exc_info=True)
        raise


def write_stream_of_obj(obj_stream: Iterable[dict], output_file: str | None = None):
    try:
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                for obj in obj_stream:
                    f.write(json.dumps(obj))
                    f.write('\n')
        else:
            for obj in obj_stream:
                sys.stdout.write(json.dumps(obj))
                sys.stdout.write('\n')
    except IOError:
        logger.error(f'Error writing stream to {output_file or "stdout"}', exc_info=True)
        raise
