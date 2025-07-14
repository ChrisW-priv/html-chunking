#!/usr/bin/env python3
import sys
import argparse
import hashlib
from common import read_input, write_output
from operator import le


def shorten_text(text: str, max_elements: int = 2, subsections: list[dict[str, object]] | None = None) -> str:
    """Shorten text by splitting on lines and keeping at most max_elements, appending '...' if truncated."""
    if max_elements == -1:
        return text

    if not text:
        result = ""
        for child in subsections or []:
            result = "<p>Covered topics in this subsection:</p><ul>"
            for child in subsections or []:
                result += f"<li>{child.get('title', '')}</li>"
            result += "</ul>"
        return result

    DELIM = ""
    lines = text.splitlines()
    if len(lines) <= max_elements:
        if subsections:
            lines.append("...")
        return DELIM.join(lines)
    shortened = lines[:max_elements]
    shortened.append("...")
    return DELIM.join(shortened)


def generate_section_digest(node: dict[str, str | list[dict]]) -> dict[str, object]:
    """Generate a section digest string for a node, including its title/text and immediate children."""
    text = node.get("text", "")
    section_digest = {
        "title": node.get("title", ""),
        "text": text,
        "subsections": []
    }
    # Include immediate children
    for child in node.get("subsections", []):
        child_title = child.get("title", "")
        child_text = child.get("text", "")
        child_subsections = child.get("subsections")
        length = 1 if text else -1
        short_text = shorten_text(child_text, length, child_subsections)
        section_digest["subsections"].append({
            "title": child_title,
            "text": short_text
        })
    return section_digest


def compute_id(section_digest: dict[str, object]) -> str:
    """Compute a BLAKE2b hash of the section digest text as the node ID."""
    h = hashlib.blake2b(digest_size=16)
    section_digest_text = str(section_digest)
    h.update(section_digest_text.encode("utf-8"))
    return h.hexdigest()


def process_node(
    node: dict[str, object], parent_id: str | None = None
) -> list[dict[str, object]]:
    """
    Recursively process a node and its subsections, returning a flat list of nodes
    with 'id', 'parent_id', 'title', 'text', and 'summary'.
    """
    section_digest = generate_section_digest(node)
    node_id = compute_id(section_digest)
    result: dict[str, object] = {
        "id": node_id,
        "parent_id": parent_id,
        "title": node.get("title"),
        "text": node.get("text"),
        "section_digest": section_digest,
    }
    nodes: list[dict[str, object]] = [result]
    for child in node.get("subsections", []):  # type: ignore
        nodes.extend(process_node(child, parent_id=node_id))
    return nodes


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Split hierarchical JSON into JSON Lines with node summaries and IDs."
        )
    )
    parser.add_argument(
        'input', nargs='?', help="Input JSON file (defaults to stdin)"
    )
    parser.add_argument(
        '-o', '--output', help="Output JSONL file (defaults to stdout)"
    )
    args = parser.parse_args()
    try:
        data = read_input(args.input)
        nodes = process_node(data, parent_id=None)
        write_output(nodes, args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
