import pytest
from content_extraction.semantic_chunk_html import HTMLSectionParser


class TestHTMLSectionParser:
    """Comprehensive test suite for HTMLSectionParser."""

    def setup_method(self):
        self.parser = HTMLSectionParser()

    @pytest.mark.parametrize(
        "html_input,expected_output,test_description",
        [
            # Basic heading hierarchy
            (
                """
            <div>
                <h1>Main Title</h1>
                <p>Introduction text.</p>
                <h2>Subsection Title</h2>
                <p>Subsection content.</p>
            </div>
            """,
                [
                    {
                        "title": "Main Title",
                        "text": "<p>Introduction text.</p>",
                        "level": 1,
                        "subsections": [
                            {
                                "title": "Subsection Title",
                                "text": "<p>Subsection content.</p>",
                                "level": 2,
                                "subsections": [],
                            }
                        ],
                    }
                ],
                "basic h1/h2 hierarchy",
            ),
            # ARIA-level headings
            (
                """
            <div>
                <div role="heading" aria-level="1">Main Title</div>
                <p>Introduction text.</p>
                <div role="heading" aria-level="2">Subsection Title</div>
                <p>Subsection content.</p>
            </div>
            """,
                [
                    {
                        "title": "Main Title",
                        "text": "<p>Introduction text.</p>",
                        "level": 1,
                        "subsections": [
                            {
                                "title": "Subsection Title",
                                "text": "<p>Subsection content.</p>",
                                "level": 2,
                                "subsections": [],
                            }
                        ],
                    }
                ],
                "div elements with role=heading and aria-level",
            ),
            # ARIA-level without role
            (
                """
            <div>
                <div aria-level="1">Main Title</div>
                <p>Introduction text.</p>
                <div aria-level="2">Subsection Title</div>
                <p>Subsection content.</p>
            </div>
            """,
                [
                    {
                        "title": "Main Title",
                        "text": "<p>Introduction text.</p>",
                        "level": 1,
                        "subsections": [
                            {
                                "title": "Subsection Title",
                                "text": "<p>Subsection content.</p>",
                                "level": 2,
                                "subsections": [],
                            }
                        ],
                    }
                ],
                "elements with aria-level but no role=heading",
            ),
            # Mixed heading types
            (
                """
            <div>
                <h1>Main Title</h1>
                <p>Introduction text.</p>
                <div role="heading" aria-level="2">Subsection Title</div>
                <p>Subsection content.</p>
                <h3>Sub-subsection</h3>
                <p>Sub-subsection content.</p>
            </div>
            """,
                [
                    {
                        "title": "Main Title",
                        "text": "<p>Introduction text.</p>",
                        "level": 1,
                        "subsections": [
                            {
                                "title": "Subsection Title",
                                "text": "<p>Subsection content.</p>",
                                "level": 2,
                                "subsections": [
                                    {
                                        "title": "Sub-subsection",
                                        "text": "<p>Sub-subsection content.</p>",
                                        "level": 3,
                                        "subsections": [],
                                    }
                                ],
                            }
                        ],
                    }
                ],
                "mixing standard headings with aria-level headings",
            ),
            # Multiple top-level sections
            (
                """
            <div>
                <h1>First Section</h1>
                <p>First content.</p>
                <h1>Second Section</h1>
                <p>Second content.</p>
            </div>
            """,
                [
                    {
                        "title": "First Section",
                        "text": "<p>First content.</p>",
                        "level": 1,
                        "subsections": [],
                    },
                    {
                        "title": "Second Section",
                        "text": "<p>Second content.</p>",
                        "level": 1,
                        "subsections": [],
                    },
                ],
                "multiple sections at the same level",
            ),
            # Complex nesting
            (
                """
            <div>
                <h1>Chapter 1</h1>
                <p>Chapter intro.</p>
                <h2>Section 1.1</h2>
                <p>Section content.</p>
                <h3>Subsection 1.1.1</h3>
                <p>Subsection content.</p>
                <h2>Section 1.2</h2>
                <p>Another section.</p>
                <h1>Chapter 2</h1>
                <p>Second chapter.</p>
            </div>
            """,
                [
                    {
                        "title": "Chapter 1",
                        "text": "<p>Chapter intro.</p>",
                        "level": 1,
                        "subsections": [
                            {
                                "title": "Section 1.1",
                                "text": "<p>Section content.</p>",
                                "level": 2,
                                "subsections": [
                                    {
                                        "title": "Subsection 1.1.1",
                                        "text": "<p>Subsection content.</p>",
                                        "level": 3,
                                        "subsections": [],
                                    }
                                ],
                            },
                            {
                                "title": "Section 1.2",
                                "text": "<p>Another section.</p>",
                                "level": 2,
                                "subsections": [],
                            },
                        ],
                    },
                    {
                        "title": "Chapter 2",
                        "text": "<p>Second chapter.</p>",
                        "level": 1,
                        "subsections": [],
                    },
                ],
                "complex nested structure",
            ),
            # Empty sections
            (
                """
            <div>
                <h1>Empty Section</h1>
                <h2>Empty Subsection</h2>
                <h1>Another Empty Section</h1>
            </div>
            """,
                [
                    {
                        "title": "Empty Section",
                        "text": "",
                        "level": 1,
                        "subsections": [
                            {
                                "title": "Empty Subsection",
                                "text": "",
                                "level": 2,
                                "subsections": [],
                            }
                        ],
                    },
                    {
                        "title": "Another Empty Section",
                        "text": "",
                        "level": 1,
                        "subsections": [],
                    },
                ],
                "sections with no content",
            ),
            # No headings
            (
                """
            <div>
                <p>Just some content.</p>
                <p>No headings here.</p>
            </div>
            """,
                [],
                "HTML with no headings",
            ),
            # Role heading without aria-level
            (
                """
            <div>
                <div role="heading">Main Title</div>
                <p>Content here.</p>
            </div>
            """,
                [
                    {
                        "title": "Main Title",
                        "text": "<p>Content here.</p>",
                        "level": 1,
                        "subsections": [],
                    }
                ],
                "role=heading without aria-level (should default to level 1)",
            ),
            # Multiple content elements
            (
                """
            <div>
                <h1>Main Title</h1>
                <p>First paragraph.</p>
                <div>Some div content.</div>
                <ul><li>List item</li></ul>
                <h2>Subsection</h2>
                <p>Subsection content.</p>
            </div>
            """,
                [
                    {
                        "title": "Main Title",
                        "text": "<p>First paragraph.</p><div>Some div content.</div><ul><li>List item</li></ul>",
                        "level": 1,
                        "subsections": [
                            {
                                "title": "Subsection",
                                "text": "<p>Subsection content.</p>",
                                "level": 2,
                                "subsections": [],
                            }
                        ],
                    }
                ],
                "sections with multiple content elements",
            ),
        ],
    )
    def test_parse_sections(self, html_input, expected_output, test_description):
        """Parametrized test for various HTML section parsing scenarios."""
        result = self.parser.parse_sections(html_input)
        assert result == expected_output, f"Failed test: {test_description}"
