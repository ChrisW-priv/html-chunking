"""
DSPy modules for enriching nodes with additional fields derived from section_digest.
"""

import dspy
import json
from typing import List, Dict, Any, Optional

# This helper function is used to format the section_digest dictionary
# into a single string that can be passed to the language model.
def format_section_digest(section_digest: Dict[str, Any]) -> str:
    """Converts section_digest dict to a string for the LLM."""
    content = f"Title: {section_digest.get('title', 'No title')}\n"
    content += f"Text: {section_digest.get('text', 'No text')}\n"

    if 'subsections' in section_digest and section_digest['subsections']:
        content += "\nSubsections:\n"
        for i, subsection in enumerate(section_digest['subsections'], 1):
            content += f"{i}. {subsection.get('title', 'Untitled')}\n"
            content += f"   {subsection.get('text', 'No text')}\n"
    return content

# --- Individual Field Signatures ---

class GenerateTitle(dspy.Signature):
    """Generate a clear, concise title for the node."""
    section_content = dspy.InputField(desc="The content of the section.")
    title = dspy.OutputField(desc="A clear, concise title that defines the node.")

class CleanText(dspy.Signature):
    """Clean and process the text content."""
    section_content = dspy.InputField(desc="The content of the section.")
    text = dspy.OutputField(desc="The text content, cleaned and processed.")

class ExtractDefinitions(dspy.Signature):
    """Extract key concepts and their definitions as a JSON array."""
    section_content = dspy.InputField(desc="The content of the section.")
    definitions = dspy.OutputField(desc="A JSON array of objects, each with 'term' and 'explanation'.")

class ExtractProcedures(dspy.Signature):
    """Extract step-by-step instructions as a JSON array."""
    section_content = dspy.InputField(desc="The content of the section.")
    procedures = dspy.OutputField(desc="A JSON array of strings for step-by-step instructions.")

class GenerateKeywords(dspy.Signature):
    """Generate keywords or phrases as a JSON array."""
    section_content = dspy.InputField(desc="The content of the section.")
    keywords = dspy.OutputField(desc="A JSON array of strings for search keywords.")

class GenerateFlashcards(dspy.Signature):
    """Generate question-answer pairs as a JSON array."""
    section_content = dspy.InputField(desc="The content of the section.")
    flashcards = dspy.OutputField(desc="A JSON array of objects, each with 'question' and 'answer'.")

class GenerateAbstract(dspy.Signature):
    """Generate a brief summary of the main points."""
    section_content = dspy.InputField(desc="The content of the section.")
    abstract = dspy.OutputField(desc="A brief summary (2-3 sentences).")

class GenerateFocus(dspy.Signature):
    """Describe the main focus or purpose of the content."""
    section_content = dspy.InputField(desc="The content of the section.")
    focus = dspy.OutputField(desc="The main focus or purpose (1 sentence).")

# --- Main DSPy Module ---

class EnrichNodeWithDSPy(dspy.Module):
    """A DSPy module to enrich a node with various fields from its section_digest."""
    def __init__(self):
        super().__init__()
        self.generate_title = dspy.Predict(GenerateTitle)
        self.clean_text = dspy.Predict(CleanText)
        self.extract_definitions = dspy.Predict(ExtractDefinitions)
        self.extract_procedures = dspy.Predict(ExtractProcedures)
        self.generate_keywords = dspy.Predict(GenerateKeywords)
        self.generate_flashcards = dspy.Predict(GenerateFlashcards)
        self.generate_abstract = dspy.Predict(GenerateAbstract)
        self.generate_focus = dspy.Predict(GenerateFocus)

    def forward(self, section_digest: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes a section_digest dictionary and returns a dictionary of enriched fields.
        This performs a separate LLM call for each field, which can be slow and expensive.
        """
        section_content = format_section_digest(section_digest)

        # Making individual calls for each field
        title = self.generate_title(section_content=section_content).title
        text = self.clean_text(section_content=section_content).text
        definitions_str = self.extract_definitions(section_content=section_content).definitions
        procedures_str = self.extract_procedures(section_content=section_content).procedures
        keywords_str = self.generate_keywords(section_content=section_content).keywords
        flashcards_str = self.generate_flashcards(section_content=section_content).flashcards
        abstract = self.generate_abstract(section_content=section_content).abstract
        focus = self.generate_focus(section_content=section_content).focus

        # Helper to parse JSON fields safely
        def safe_json_loads(data, default_value):
            try:
                # The output might be a string that looks like a list of dicts, so json.loads is appropriate
                return json.loads(data)
            except (json.JSONDecodeError, TypeError):
                # If it fails, it might just be a plain string. Or malformed.
                # Returning a default value is a safe fallback.
                return default_value

        return {
            "title": title,
            "text": text,
            "definitions": safe_json_loads(definitions_str, []),
            "procedures": safe_json_loads(procedures_str, []),
            "keywords": safe_json_loads(keywords_str, []),
            "flashcards": safe_json_loads(flashcards_str, []),
            "abstract": abstract,
            "focus": focus,
        }
