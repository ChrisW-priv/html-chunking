#!/usr/bin/env python3
import sys
import argparse
import hashlib
from common import read_input, write_output


def shorten_text(text: str, max_elements: int = 2, has_children: bool = False) -> str:
    """Shorten text by splitting on lines and keeping at most max_elements, appending '...' if truncated."""
    DELIM = ""
    lines = text.splitlines()
    if len(lines) <= max_elements:
        if has_children:
            lines.append("...")
        return DELIM.join(lines)
    shortened = lines[:max_elements]
    shortened.append("...")
    return DELIM.join(shortened)


def generate_section_digest(node: dict[str, object]) -> dict[str, object]:
    """Generate a section digest string for a node, including its title/text and immediate children."""
    section_digest = {
        "title": node.get("title", ""),
        "text": node.get("text", ""),
        "subsections": []
    }
    # Include immediate children
    for child in node.get("subsections", []):  # type: ignore
        child_title = child.get("title", "")
        child_text = child.get("text", "")
        child_has_children = child.get("subsections", False)
        short_text = shorten_text(child_text, 1, child_has_children)
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
