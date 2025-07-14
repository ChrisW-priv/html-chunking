"""
Training script for DSPy modules to generate enrichment models.

This script simulates a "training" process for the DSPy predictors
defined in `dspy_modules.py`. In DSPy, this process is called "compilation."

The script does the following:
1.  Sets up a language model (e.g., OpenAI's GPT).
2.  Loads mock "training" data. In a real-world scenario, this would be a
    well-curated dataset of input-output examples.
3.  Uses a DSPy optimizer (`BootstrapFewShot`) to compile each predictor.
    This process creates effective few-shot prompts based on the training data.
4.  Saves the compiled state of each predictor to a separate JSON file in the
    `dspy_models/` directory. These JSON files represent the "trained" models
    that can be loaded for inference later.

To run this script:
1.  Make sure you have an OpenAI API key set as an environment variable:
    export OPENAI_API_KEY="your-api-key"
2.  Run the script from the project root directory:
    python content-extraction/train_dspy_modules.py
"""

import dspy
import os
import json
from dspy_modules import (
    GenerateTitle,
    CleanText,
    ExtractDefinitions,
    ExtractProcedures,
    GenerateKeywords,
    GenerateFlashcards,
    GenerateAbstract,
    GenerateFocus,
    format_section_digest
)

# --- Mock Training Data ---
# This data simulates a training set. In a real scenario, you would have
# many more examples to help the optimizer create robust prompts.

# A shared, representative input example
mock_section_digest = {
    "title": "Introduction to Quantum Computing",
    "text": "Quantum computing is a type of computation that harnesses the collective properties of quantum states, such as superposition, interference, and entanglement, to perform calculations. The devices that perform quantum computations are known as quantum computers.",
    "subsections": [
        {
            "title": "Qubits",
            "text": "The basic unit of quantum information is the qubit, which is analogous to the classical bit. A qubit can be in a 1 or 0 quantum state, or in a superposition of both states."
        }
    ]
}

# Format the digest into a single string input for the models
section_content_input = format_section_digest(mock_section_digest)

# Create a training set for each field to be generated.
# Each example pairs an input with a desired, high-quality output.

title_trainset = [
    dspy.Example(section_content=section_content_input, title="Introduction to Quantum Computing").with_inputs("section_content")
]

text_trainset = [
    dspy.Example(section_content=section_content_input, text="Quantum computing utilizes quantum-mechanical phenomena like superposition, interference, and entanglement to process information. The fundamental unit is the qubit, which can exist in multiple states simultaneously.").with_inputs("section_content")
]

definitions_trainset = [
    dspy.Example(section_content=section_content_input, definitions=json.dumps([
        {"term": "Quantum Computing", "explanation": "A computation type using quantum states (superposition, etc.) for calculations."},
        {"term": "Qubit", "explanation": "The basic unit of quantum information, analogous to a bit."}
    ])).with_inputs("section_content")
]

procedures_trainset = [
    dspy.Example(section_content="To make a cup of tea, first boil water. Then, pour the water into a cup with a tea bag. Finally, let it steep for 3-5 minutes.", procedures=json.dumps([
        "Boil water.",
        "Pour water into a cup with a tea bag.",
        "Let it steep for 3-5 minutes."
    ])).with_inputs("section_content")
]

keywords_trainset = [
    dspy.Example(section_content=section_content_input, keywords=json.dumps(["Quantum Computing", "Qubit", "Superposition", "Entanglement"])).with_inputs("section_content")
]

flashcards_trainset = [
    dspy.Example(section_content=section_content_input, flashcards=json.dumps([
        {"question": "What is the basic unit of quantum information?", "answer": "The qubit."},
        {"question": "What is quantum computing?", "answer": "A type of computation that uses quantum states to perform calculations."}
    ])).with_inputs("section_content")
]

abstract_trainset = [
    dspy.Example(section_content=section_content_input, abstract="This section introduces quantum computing, explaining its reliance on quantum phenomena like superposition and entanglement. It also defines the qubit as the fundamental unit of quantum information.").with_inputs("section_content")
]

focus_trainset = [
    dspy.Example(section_content=section_content_input, focus="To provide a foundational understanding of what quantum computing is and its basic components.").with_inputs("section_content")
]


def main():
    """
    Main function to "train" and save DSPy modules for each enrichment field.
    """
    print("Starting DSPy model compilation process...")

    # 1. Setup the language model
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\nError: OPENAI_API_KEY environment variable is required.")
        print("Please set the variable and try again: export OPENAI_API_KEY='your-key'\n")
        return

    lm = dspy.llms.OpenAI(model='gpt-4o-mini', max_tokens=2000, api_key=api_key)
    dspy.settings.configure(lm=lm)

    # 2. Define all modules to be trained
    modules_to_train = [
        {"name": "title", "signature": GenerateTitle, "trainset": title_trainset},
        {"name": "text", "signature": CleanText, "trainset": text_trainset},
        {"name": "definitions", "signature": ExtractDefinitions, "trainset": definitions_trainset},
        {"name": "procedures", "signature": ExtractProcedures, "trainset": procedures_trainset},
        {"name": "keywords", "signature": GenerateKeywords, "trainset": keywords_trainset},
        {"name": "flashcards", "signature": GenerateFlashcards, "trainset": flashcards_trainset},
        {"name": "abstract", "signature": GenerateAbstract, "trainset": abstract_trainset},
        {"name": "focus", "signature": GenerateFocus, "trainset": focus_trainset},
    ]

    # 3. Create output directory relative to this script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "dspy_models")
    os.makedirs(output_dir, exist_ok=True)
    print(f"\nModels will be saved in: '{os.path.relpath(output_dir)}'")

    # 4. Compile and save each module
    for module_info in modules_to_train:
        name = module_info["name"]
        signature = module_info["signature"]
        trainset = module_info["trainset"]

        print(f"\n--- Compiling module for: '{name}' ---")

        predictor = dspy.Predict(signature)
        optimizer = dspy.BootstrapFewShot(metric=None, max_bootstrapped_demos=1)

        try:
            optimized_predictor = optimizer.compile(predictor, trainset=trainset)
            model_path = os.path.join(output_dir, f"{name}_model.json")
            optimized_predictor.save(model_path)
            print(f"Successfully compiled and saved model to '{os.path.relpath(model_path)}'")
        except Exception as e:
            print(f"ERROR: Could not compile module for '{name}'. Reason: {e}")

    print("\nCompilation process finished.\n")


if __name__ == "__main__":
    main()
