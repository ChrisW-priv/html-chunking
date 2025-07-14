"""
CLI tool to enrich nodes using trained DSPy models.

This script takes JSONL input (each line is a JSON object representing a node)
and enriches each node with the following fields using pre-compiled DSPy models:

- Title
- Text
- Definitions
- Procedures
- Keywords
- Flashcards
- Abstract
- Focus
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Any, Optional

import dspy
from common_std_io import write_output
from dspy_modules import (
    ExtractDefinitions,
    ExtractProcedures,
    GenerateKeywords,
    GenerateFlashcards,
    GenerateAbstract,
    GenerateFocus,
)


def setup_dspy_lm() -> None:
    """Initialize and configure the DSPy language model."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")

    lm = dspy.LM("openai/gpt-4o-mini", api_key=api_key)
    dspy.settings.configure(lm=lm)


def load_dspy_models(models_dir: str) -> Dict[str, dspy.Predict]:
    """Load all compiled DSPy models from the specified directory."""

    model_signatures = {
        "title": GenerateTitle,
        "text": CleanText,
        "definitions": ExtractDefinitions,
        "procedures": ExtractProcedures,
        "keywords": GenerateKeywords,
        "flashcards": GenerateFlashcards,
        "abstract": GenerateAbstract,
        "focus": GenerateFocus,
    }

    loaded_models = {}
    print(f"Loading models from: {models_dir}", file=sys.stderr)

    for name, signature in model_signatures.items():
        model_path = os.path.join(models_dir, f"{name}_model.json")
        predictor = dspy.Predict(signature)

        if os.path.exists(model_path):
            try:
                # Load compiled model state if it exists
                predictor.load(model_path)
                print(f"-> Loaded compiled model for '{name}'", file=sys.stderr)
            except Exception as e:
                # Handle corrupted or invalid model files
                print(
                    f"Warning: Failed to load model for '{name}' from {model_path}. "
                    f"Using an untrained default. Error: {e}",
                    file=sys.stderr,
                )
        else:
            # If the model file doesn't exist, use the uncompiled predictor
            print(
                f"Warning: Model for '{name}' not found at {model_path}. "
                f"Using an untrained default. "
                f"Run `train_dspy_modules.py` to compile.",
                file=sys.stderr,
            )

        loaded_models[name] = predictor

    return loaded_models


def enrich_node_with_dspy(
    node: Dict[str, Any], models: Dict[str, dspy.Predict]
) -> Dict[str, Any]:
    """Enrich a single node using compiled DSPy models."""

    if 'section_digest' not in node:
        raise ValueError("Node must contain 'section_digest'")

    try:
        section_content = format_section_digest(node['section_digest'])

        # --- Call each model to get the enriched fields ---
        title = models['title'](section_content=section_content).title
        text = models['text'](section_content=section_content).text
        definitions_str = models['definitions'](section_content=section_content).definitions
        procedures_str = models['procedures'](section_content=section_content).procedures
        keywords_str = models['keywords'](section_content=section_content).keywords
        flashcards_str = models['flashcards'](section_content=section_content).flashcards
        abstract = models['abstract'](section_content=section_content).abstract
        focus = models['focus'](section_content=section_content).focus

        # Helper to safely parse JSON strings from model outputs
        def safe_json_loads(data: str, default_value: Any) -> Any:
            try:
                return json.loads(data)
            except (json.JSONDecodeError, TypeError):
                return default_value

        # Create the enriched node
        enriched = node.copy()

        # Update title and text if provided by LLM
        if title:
            enriched['title'] = title
        if text:
            enriched['text'] = text

        # Add enrichment fields
        enriched.update({
            'definitions': safe_json_loads(definitions_str, []),
            'procedures': safe_json_loads(procedures_str, []),
            'keywords': safe_json_loads(keywords_str, []),
            'flashcards': safe_json_loads(flashcards_str, []),
            'abstract': abstract or '',
            'focus': focus or ''
        })

        return enriched

    except Exception as e:
        print(f"Error enriching node {node.get('id', 'unknown')}: {e}", file=sys.stderr)
        # Return original node with empty enrichment fields on error
        enriched = node.copy()
        enriched.update({
            'definitions': [], 'procedures': [], 'keywords': [],
            'flashcards': [], 'abstract': '', 'focus': ''
        })
        return enriched


def process_jsonl_input(input_file: Optional[str] = None) -> List[Dict[str, Any]]:
    """Process JSONL input from a file or stdin and return a list of nodes."""
    nodes = []
    try:
        lines = []
        if input_file:
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = sys.stdin.readlines()
    except Exception as e:
        raise RuntimeError(f"Error reading input: {e}")

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        try:
            nodes.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON on line {line_num}: {e}", file=sys.stderr)
            continue
    return nodes


def main():
    """Main CLI function for inference."""
    parser = argparse.ArgumentParser(
        description="Enrich nodes with trained DSPy models."
    )
    parser.add_argument(
        '-i', '--input', type=str, help='Input JSONL file (default: stdin)'
    )
    parser.add_argument(
        '-o', '--output', type=str, help='Output JSONL file (default: stdout)'
    )
    parser.add_argument(
        '--api-key', type=str, help='OpenAI API key (or use OPENAI_API_KEY env var)'
    )
    parser.add_argument(
        '--models-dir', type=str, default='content-extraction/dspy_models',
        help='Directory containing the trained DSPy model .json files'
    )

    args = parser.parse_args()

    # Set up OpenAI API key
    if args.api_key:
        os.environ['OPENAI_API_KEY'] = args.api_key

    try:
        # Initialize DSPy LM
        setup_dspy_lm()

        # Load compiled DSPy models
        dspy_models = load_dspy_models(args.models_dir)

        # Process input
        nodes = process_jsonl_input(args.input)
        if not nodes:
            print("No valid nodes found in input", file=sys.stderr)
            return 1

        # Enrich each node
        enriched_nodes = []
        for i, node in enumerate(nodes, 1):
            print(f"Processing node {i}/{len(nodes)}: {node.get('id', 'unknown')}", file=sys.stderr)
            enriched_node = enrich_node_with_dspy(node, dspy_models)
            enriched_nodes.append(enriched_node)

        # Write output
        write_output(enriched_nodes, args.output)
        print(f"\nSuccessfully enriched {len(enriched_nodes)} nodes.", file=sys.stderr)

    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
