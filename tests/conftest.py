import pytest
import sys
import os
from pathlib import Path

# Add the src directory to the Python path so we can import modules
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

@pytest.fixture
def sample_html_fixtures():
    """Provide common HTML fixtures for testing."""
    return {
        'basic_structure': """
        <div>
            <h1>Main Title</h1>
            <p>Introduction paragraph.</p>
            <h2>First Section</h2>
            <p>First section content.</p>
            <h2>Second Section</h2>
            <p>Second section content.</p>
            <section>
                <h2>Third Section</h2>
                <p>Third section already wrapped.</p>
            </section>
        </div>
        """,

        'aria_overrides': """
        <div>
            <h1>Main Title</h1>
            <h6 aria-level="2">Override H2</h6>
            <p>Content with aria-level override.</p>
            <h3 aria-level="7">Deep Override</h3>
            <p>Content with deep aria-level override.</p>
        </div>
        """,

        'custom_headings': """
        <div>
            <h1>Main Title</h1>
            <div role="heading" aria-level="2">Custom Heading Level 2</div>
            <p>Content under custom heading.</p>
            <div role="heading" aria-level="10">Very Deep Custom Heading</div>
            <p>Content under very deep custom heading.</p>
        </div>
        """,

        'mixed_content': """
        <div>
            <h1>Document with Mixed Content</h1>
            <p>Introduction paragraph.</p>
            <ul>
                <li>List item 1</li>
                <li>List item 2</li>
            </ul>
            <h2>Section with Table</h2>
            <table>
                <tr><td>Cell 1</td><td>Cell 2</td></tr>
            </table>
            <h2>Section with List</h2>
            <ol>
                <li>Ordered item 1</li>
                <li>Ordered item 2</li>
            </ol>
        </div>
        """
    }

@pytest.fixture
def parser():
    """Provide a parser instance for testing."""
    from content_extraction.semantic_chunk_html import SectionParser
    return SectionParser()

# Configure pytest to show more verbose output
def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
