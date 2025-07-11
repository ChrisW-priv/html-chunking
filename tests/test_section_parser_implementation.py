import pytest
from pathlib import Path
from bs4 import BeautifulSoup
from content_extraction import SectionParser


class TestSectionParserImplementation:
    """Test the section parser implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = SectionParser()

    @pytest.mark.parametrize("html,expected_level", [
        # Standard heading tags
        ('<h1>Test</h1>', 1),
        ('<h2>Test</h2>', 2),
        ('<h3>Test</h3>', 3),
        ('<h4>Test</h4>', 4),
        ('<h5>Test</h5>', 5),
        ('<h6>Test</h6>', 6),

        # Aria-level overrides on standard headings
        ('<h1 aria-level="3">Test</h1>', 3),
        ('<h2 aria-level="1">Test</h2>', 1),
        ('<h6 aria-level="2">Test</h6>', 2),
        ('<h3 aria-level="7">Test</h3>', 7),
        ('<h4 aria-level="100">Test</h4>', 100),

        # Div elements with role='heading'
        ('<div role="heading" aria-level="1">Test</div>', 1),
        ('<div role="heading" aria-level="2">Test</div>', 2),
        ('<div role="heading" aria-level="10">Test</div>', 10),
        ('<div role="heading" aria-level="999">Test</div>', 999),

        # Edge cases with aria-level parsing
        ('<h1 aria-level="invalid">Test</h1>', 1),  # Invalid aria-level falls back to tag level
        ('<h2 aria-level="">Test</h2>', 2),  # Empty aria-level falls back to tag level
        ('<h3 aria-level="0">Test</h3>', 0),  # Zero aria-level
        ('<h4 aria-level="-1">Test</h4>', -1),  # Negative aria-level

        # Non-heading elements
        ('<p>Test</p>', None),
        ('<div>Test</div>', None),
        ('<span>Test</span>', None),
        ('<div role="button">Test</div>', None),

        # Div with heading role but no aria-level
        ('<div role="heading">Test</div>', None),

        # Invalid custom heading with invalid aria-level
        ('<div role="heading" aria-level="invalid">Test</div>', None),
    ])
    def test_get_aria_level_headings(self, html, expected_level):
        """Test aria level detection for valid heading elements."""
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find()
        assert self.parser.get_aria_level(element) == expected_level

    @pytest.mark.parametrize("html,expected_result", [
        # Valid heading elements
        ('<h1>Test</h1>', True),
        ('<h2 aria-level="3">Test</h2>', True),
        ('<div role="heading" aria-level="2">Test</div>', True),

        # Non-heading elements
        ('<p>Test</p>', False),
        ('<div>Test</div>', False),
        ('<div role="heading">Test</div>', False),  # No aria-level
    ])
    def test_is_heading_method(self, html, expected_result):
        """Test the is_heading method."""
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find()
        assert self.parser.is_heading(element) == expected_result

    def test_extract_text_content(self):
        """Test text content extraction from p tags."""
        html = """
        <div>
            <h2>Title</h2>
            <p>First paragraph.</p>
            <p>Second paragraph.</p>
            <ul>
                <li>List item 1</li>
                <li>List item 2</li>
            </ul>
            <blockquote>Quote content.</blockquote>
        </div>
        """
        soup = BeautifulSoup(html, 'html.parser')
        div_element = soup.find('div')

        text_content = self.parser.extract_text_content(div_element)

        assert 'First paragraph.' in text_content
        assert 'Second paragraph.' in text_content
        assert 'List item 1' in text_content
        assert 'Quote content.' in text_content

    def test_find_highest_aria_element(self):
        """Test finding the highest aria element."""
        html = """
        <div>
            <h2>H2 Title</h2>
            <h1>H1 Title</h1>
            <h3>H3 Title</h3>
            <div role="heading" aria-level="1">Custom H1</div>
        </div>
        """
        soup = BeautifulSoup(html, 'html.parser')
        root_element = soup.find('div')

        highest = self.parser.find_highest_aria_element(root_element)

        # Should find either h1 or the custom div with aria-level="1"
        assert highest is not None
        assert self.parser.get_aria_level(highest) == 1

    @pytest.mark.parametrize("html,level,expected_count", [
        # Case 0: No headings at specified level
        ("""
        <div>
            <h1>H1 Title</h1>
            <h2>H2 Title</h2>
            <h3>H3 Title</h3>
        </div>
        """, 4, 0),

        # Case 1: Exactly one heading at level
        ("""
        <div>
            <h1>Only H1</h1>
            <h2>H2 Title</h2>
            <h3>H3 Title</h3>
        </div>
        """, 1, 1),

        # Case >1: Multiple headings at same level
        ("""
        <div>
            <h1>H1 Title</h1>
            <h2>First H2</h2>
            <h2>Second H2</h2>
            <h6 aria-level="2">H6 Override</h6>
            <div role="heading" aria-level="2">Custom H2</div>
            <h3>H3 Title</h3>
        </div>
        """, 2, 4),

        # Case 0: No headings at all
        ("""
        <div>
            <p>Just text content</p>
            <span>More text</span>
        </div>
        """, 1, 0),

        # Case 1: Single custom heading with aria-level
        ("""
        <div>
            <div role="heading" aria-level="5">Custom H5</div>
            <p>Content</p>
        </div>
        """, 5, 1),

        # Case >1: Multiple headings with aria-level overrides
        ("""
        <div>
            <h1 aria-level="3">H1 Override</h1>
            <h2 aria-level="3">H2 Override</h2>
            <h3>Regular H3</h3>
            <div role="heading" aria-level="3">Custom H3</div>
        </div>
        """, 3, 4),

        # Case 0: Search for level that doesn't exist due to aria overrides
        ("""
        <div>
            <h1 aria-level="2">H1 Override</h1>
            <h2 aria-level="3">H2 Override</h2>
        </div>
        """, 1, 0),
    ])
    def test_get_all_headings_at_level_parametrized(self, html, level, expected_count):
        """Test getting all headings at a specific level with various scenarios."""
        soup = BeautifulSoup(html, 'html.parser')
        root_element = soup.find('div')

        headings = list(self.parser.get_all_headings_at_level(root_element, level))

        assert len(headings) == expected_count

    @pytest.mark.parametrize("html,expected_result", [
        # Base case: container with single heading and text content
        ("""
        <div>
            <h3>Simple Header</h3>
            <p>Just text content.</p>
        </div>
        """, True),

        # Base case: container with single heading and no content
        ("""
        <div>
            <h2>Only Header</h2>
        </div>
        """, True),

        # Base case: container with single heading and multiple text elements
        ("""
        <div>
            <h1>Header</h1>
            <p>Paragraph 1</p>
            <p>Paragraph 2</p>
            <ul><li>List item</li></ul>
            <blockquote>Quote</blockquote>
        </div>
        """, True),

        # Non-base case: container with multiple headings
        ("""
        <div>
            <h2>Header</h2>
            <p>Some content.</p>
            <h3>Nested Header</h3>
            <p>More content.</p>
        </div>
        """, False),

        # Non-base case: container with multiple headings at same level
        ("""
        <div>
            <h1>Main Header</h1>
            <p>Content</p>
            <h2>Sub Header 1</h2>
            <h2>Sub Header 2</h2>
        </div>
        """, False),

        # Non-base case: container with standard and custom headings
        ("""
        <div>
            <h2>Standard Header</h2>
            <p>Content</p>
            <div role="heading" aria-level="3">Custom Header</div>
        </div>
        """, False),

        # Base case: container with single custom heading and text content
        ("""
        <div>
            <div role="heading" aria-level="2">Custom Header</div>
            <p>Just text content.</p>
        </div>
        """, True),

        # Non-base case: container with multiple custom headings
        ("""
        <div>
            <div role="heading" aria-level="1">Custom Header</div>
            <p>Content</p>
            <h2>Nested Header</h2>
        </div>
        """, False),

        # Base case: section with single heading
        ("""
        <section>
            <h2>Section Header</h2>
            <p>Section content.</p>
        </section>
        """, True),

        # Non-base case: section with multiple headings
        ("""
        <section>
            <h1>Main Header</h1>
            <h2>Sub Header</h2>
            <p>Content</p>
        </section>
        """, False),
    ])
    def test_is_base_case(self, html, expected_result):
        """Test base case detection on entire container elements."""
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find(['div', 'section'])

        assert self.parser.is_base_case(element) == expected_result

    def test_is_already_wrapped_in_section(self):
        """Test detection of elements already wrapped in sections."""
        html = """
        <div>
            <h2>Unwrapped H2</h2>
            <section>
                <h2>Wrapped H2</h2>
                <p>Content</p>
            </section>
        </div>
        """
        soup = BeautifulSoup(html, 'html.parser')

        unwrapped_h2 = soup.find('h2')
        wrapped_h2 = soup.find('section').find('h2')

        assert self.parser.is_already_wrapped_in_section(unwrapped_h2) == False
        assert self.parser.is_already_wrapped_in_section(wrapped_h2) == True

    @pytest.mark.parametrize("html,expected_result", [
        # Base case: single heading with text content
        ("""
        <div>
            <h2>Simple Title</h2>
            <p>First paragraph content.</p>
            <p>Second paragraph content.</p>
        </div>
        """, {
            'title': 'Simple Title',
            'text': '<p>First paragraph content.</p>\n<p>Second paragraph content.</p>',
            'level': 2,
            'subsections': []
        }),

        # Base case: single heading with no text content
        ("""
        <div>
            <h1>Just a Title</h1>
        </div>
        """, {
            'title': 'Just a Title',
            'text': '',
            'level': 1,
            'subsections': []
        }),

        # Base case: single custom heading with text
        ("""
        <div>
            <div role="heading" aria-level="3">Custom Header</div>
            <p>Some content here.</p>
            <ul><li>List item</li></ul>
        </div>
        """, {
            'title': 'Custom Header',
            'text': '<p>Some content here.</p>\n<ul><li>List item</li></ul>',
            'level': 3,
            'subsections': []
        }),

        # Nested case: main heading with one subsection
        ("""
        <div>
            <h1>Main Title</h1>
            <p>Introduction text.</p>
            <h2>Subsection Title</h2>
            <p>Subsection content.</p>
        </div>
        """, {
            'title': 'Main Title',
            'text': '<p>Introduction text.</p>',
            'level': 1,
            'subsections': [{
                'title': 'Subsection Title',
                'text': '<p>Subsection content.</p>',
                'level': 2,
                'subsections': []
            }]
        }),

        # Nested case: main heading with multiple subsections
        ("""
        <div>
            <h1>Main Title</h1>
            <p>Main content.</p>
            <h2>First Subsection</h2>
            <p>First subsection content.</p>
            <h2>Second Subsection</h2>
            <p>Second subsection content.</p>
        </div>
        """, {
            'title': 'Main Title',
            'text': '<p>Main content.</p>',
            'level': 1,
            'subsections': [
                {
                    'title': 'First Subsection',
                    'text': '<p>First subsection content.</p>',
                    'level': 2,
                    'subsections': []
                },
                {
                    'title': 'Second Subsection',
                    'text': '<p>Second subsection content.</p>',
                    'level': 2,
                    'subsections': []
                }
            ]
        }),

        # Complex nested case: multiple levels
        ("""
        <div>
            <h1>Main Title</h1>
            <p>Main introduction.</p>
            <h2>Section A</h2>
            <p>Section A content.</p>
            <h3>Section A.1</h3>
            <p>Section A.1 content.</p>
            <h2>Section B</h2>
            <p>Section B content.</p>
        </div>
        """, {
            'title': 'Main Title',
            'text': '<p>Main introduction.</p>',
            'level': 1,
            'subsections': [
                {
                    'title': 'Section A',
                    'text': '<p>Section A content.</p>',
                    'level': 2,
                    'subsections': [{
                        'title': 'Section A.1',
                        'text': '<p>Section A.1 content.</p>',
                        'level': 3,
                        'subsections': []
                    }]
                },
                {
                    'title': 'Section B',
                    'text': '<p>Section B content.</p>',
                    'level': 2,
                    'subsections': []
                }
            ]
        }),

        # Mixed heading types
        ("""
        <div>
            <div role="heading" aria-level="1">Custom Main</div>
            <p>Main text.</p>
            <h2>Standard Sub</h2>
            <p>Sub text.</p>
        </div>
        """, {
            'title': 'Custom Main',
            'text': '<p>Main text.</p>',
            'level': 1,
            'subsections': [{
                'title': 'Standard Sub',
                'text': '<p>Sub text.</p>',
                'level': 2,
                'subsections': []
            }]
        }),

        # No headings case
        ("""
        <div>
            <p>Just some text.</p>
            <p>More text.</p>
        </div>
        """, {
            'title': '',
            'text': '<p>Just some text.</p>\n<p>More text.</p>',
            'level': None,
            'subsections': []
        }),

        # Test div filtering behavior
        ("""
        <div>
            <h1>Main Title</h1>
            <p>Paragraph content.</p>
            <div></div>
            <div>   </div>
            <div>This div has meaningful content</div>
            <div><h2>This div contains heading</h2><p>Content</p></div>
            <ul><li>List item</li></ul>
        </div>
        """, {
            'title': 'Main Title',
            'text': '<p>Paragraph content.</p>\n<div>This div has meaningful content</div>\n<ul><li>List item</li></ul>',
            'level': 1,
            'subsections': [{
                'title': 'This div contains heading',
                'text': '<p>Content</p>',
                'level': 2,
                'subsections': []
            }]
        }),

        # Test with links and various HTML elements
        ("""
        <div>
            <h1>Article Title</h1>
            <p>Introduction with <a href="https://example.com">external link</a> and <strong>bold text</strong>.</p>
            <p>More content with <em>emphasis</em> and <code>inline code</code>.</p>
            <blockquote>A quote with <a href="/internal">internal link</a></blockquote>
            <ul>
                <li>Item with <span>span element</span></li>
                <li>Item with <mark>highlighted text</mark></li>
            </ul>
        </div>
        """, {
            'title': 'Article Title',
            'text': '<p>Introduction with <a href="https://example.com">external link</a> and <strong>bold text</strong>.</p>\n<p>More content with <em>emphasis</em> and <code>inline code</code>.</p>\n<blockquote>A quote with <a href="/internal">internal link</a></blockquote>\n<ul>\n<li>Item with <span>span element</span></li>\n<li>Item with <mark>highlighted text</mark></li>\n</ul>',
            'level': 1,
            'subsections': []
        }),

        # Test div soup filtering - includes all elements with content
        ("""
        <div>
            <h1>Main Title</h1>
            <div class="container">
                <div class="wrapper">
                    <p>Actual content paragraph.</p>
                </div>
            </div>
            <div class="row">
                <div class="col">
                    <div class="spacer"></div>
                </div>
            </div>
            <div class="clearfix">   </div>
            <div>This div has meaningful content</div>
            <div class="layout">x</div>
            <p>Another paragraph.</p>
        </div>
        """, {
            'title': 'Main Title',
            'text': '<div class="container">\n<div class="wrapper">\n<p>Actual content paragraph.</p>\n</div>\n</div>\n<div>This div has meaningful content</div>\n<div class="layout">x</div>\n<p>Another paragraph.</p>',
            'level': 1,
            'subsections': []
        }),

        # Test complex HTML with various elements
        ("""
        <div>
            <h1>Documentation</h1>
            <p>Visit <a href="https://docs.example.com">our documentation</a> for more info.</p>
            <section>
                <p>Section content with <abbr title="HyperText Markup Language">HTML</abbr> and <time datetime="2023-01-01">date</time>.</p>
            </section>
            <h2>Code Examples</h2>
            <pre><code>function example() { return true; }</code></pre>
            <p>Use <kbd>Ctrl+C</kbd> to copy and <samp>output text</samp> appears here.</p>
            <h3>Math</h3>
            <p>Formula: E = mc<sup>2</sup> and H<sub>2</sub>O</p>
        </div>
        """, {
            'title': 'Documentation',
            'text': '<p>Visit <a href="https://docs.example.com">our documentation</a> for more info.</p>\n<section>\n<p>Section content with <abbr title="HyperText Markup Language">HTML</abbr> and <time datetime="2023-01-01">date</time>.</p>\n</section>',
            'level': 1,
            'subsections': [
                {
                    'title': 'Code Examples',
                    'text': '<pre><code>function example() { return true; }</code></pre>\n<p>Use <kbd>Ctrl+C</kbd> to copy and <samp>output text</samp> appears here.</p>',
                    'level': 2,
                    'subsections': [{
                        'title': 'Math',
                        'text': '<p>Formula: E = mc<sup>2</sup> and H<sub>2</sub>O</p>',
                        'level': 3,
                        'subsections': []
                    }]
                }
            ]
        }),

        # Test heavy div soup with nested structural divs
        ("""
        <div>
            <h1>Heavy Div Soup</h1>
            <div class="outer-container">
                <div class="inner-wrapper">
                    <div class="content-area">
                        <div class="row">
                            <div class="col-12">
                                <p>Buried content paragraph.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="separator"></div>
            <div class="divider">
                <div class="spacer-top"></div>
                <div class="spacer-bottom"></div>
            </div>
            <div class="grid">
                <div class="grid-item">
                    <span>Actual content in span</span>
                </div>
            </div>
        </div>
        """, {
            'title': 'Heavy Div Soup',
            'text': '<div class="outer-container">\n<div class="inner-wrapper">\n<div class="content-area">\n<div class="row">\n<div class="col-12">\n<p>Buried content paragraph.</p>\n</div>\n</div>\n</div>\n</div>\n</div>\n<div class="grid">\n<div class="grid-item">\n<span>Actual content in span</span>\n</div>\n</div>',
            'level': 1,
            'subsections': []
        }),

        # Test article and semantic elements
        ("""
        <div>
            <h1>News Article</h1>
            <article>
                <p>Article content with <cite>citation</cite> and <q>quoted text</q>.</p>
                <footer>
                    <address>Contact: <a href="mailto:author@example.com">author@example.com</a></address>
                </footer>
            </article>
            <aside>
                <p>Sidebar content with <dfn>definition</dfn> term.</p>
            </aside>
        </div>
        """, {
            'title': 'News Article',
            'text': '<article>\n<p>Article content with <cite>citation</cite> and <q>quoted text</q>.</p>\n<footer>\n<address>Contact: <a href="mailto:author@example.com">author@example.com</a></address>\n</footer>\n</article>\n<aside>\n<p>Sidebar content with <dfn>definition</dfn> term.</p>\n</aside>',
            'level': 1,
            'subsections': []
        }),

        # Test existing section elements - extract title from highest aria element
        ("""
        <section>
            <h2>Section Title</h2>
            <p>Section content with <a href="/link">link</a>.</p>
            <ul><li>List item</li></ul>
        </section>
        """, {
            'title': 'Section Title',
            'text': '<p>Section content with <a href="/link">link</a>.</p>\n<ul><li>List item</li></ul>',
            'level': 2,
            'subsections': []
        }),

        # Test section with nested content and multiple elements
        ("""
        <section>
            <h1>Main Section</h1>
            <p>Introduction paragraph.</p>
            <div>Content in div</div>
            <blockquote>Important quote</blockquote>
            <pre><code>Code example</code></pre>
        </section>
        """, {
            'title': 'Main Section',
            'text': '<p>Introduction paragraph.</p>\n<div>Content in div</div>\n<blockquote>Important quote</blockquote>\n<pre><code>Code example</code></pre>',
            'level': 1,
            'subsections': []
        }),

        # Test section with custom heading
        ("""
        <section>
            <div role="heading" aria-level="3">Custom Section Title</div>
            <p>Section content.</p>
            <span>Inline content</span>
        </section>
        """, {
            'title': 'Custom Section Title',
            'text': '<p>Section content.</p>\n<span>Inline content</span>',
            'level': 3,
            'subsections': []
        }),

        # Test section with multiple headings (should create subsections)
        ("""
        <section>
            <h1>Main Section</h1>
            <p>Main content.</p>
            <h2>Subsection</h2>
            <p>Subsection content.</p>
        </section>
        """, {
            'title': 'Main Section',
            'text': '<p>Main content.</p>',
            'level': 1,
            'subsections': [{
                'title': 'Subsection',
                'text': '<p>Subsection content.</p>',
                'level': 2,
                'subsections': []
            }]
        }),

        # Test section with no heading (should use empty title)
        ("""
        <section>
            <p>Just content without heading.</p>
            <ul><li>List item</li></ul>
        </section>
        """, {
            'title': '',
            'text': '<p>Just content without heading.</p>\n<ul><li>List item</li></ul>',
            'level': None,
            'subsections': []
        }),

        # Test article element (should work same as section)
        ("""
        <article>
            <h1>Article Title</h1>
            <p>Article content with <strong>formatting</strong>.</p>
            <footer>Article footer</footer>
        </article>
        """, {
            'title': 'Article Title',
            'text': '<p>Article content with <strong>formatting</strong>.</p>\n<footer>Article footer</footer>',
            'level': 1,
            'subsections': []
        }),

        # Test mixed content with both divs and sections
        ("""
        <div>
            <h1>Main Document</h1>
            <p>Introduction to the document.</p>
            <section>
                <h2>Technical Section</h2>
                <p>Technical content in section.</p>
            </section>
            <div class="content">
                <p>Content in regular div.</p>
            </div>
            <h2>Regular Heading</h2>
            <p>Content under regular heading.</p>
        </div>
        """, {
            'title': 'Main Document',
            'text': '<p>Introduction to the document.</p>\n<div class="content">\n<p>Content in regular div.</p>\n</div>',
            'level': 1,
            'subsections': [
                {
                    'title': 'Technical Section',
                    'text': '<p>Technical content in section.</p>',
                    'level': 2,
                    'subsections': []
                },
                {
                    'title': 'Regular Heading',
                    'text': '<p>Content under regular heading.</p>',
                    'level': 2,
                    'subsections': []
                }
            ]
        }),
    ])
    def test_parse_to_dict(self, html, expected_result):
        """Test the full parse_to_dict functionality with various scenarios."""
        soup = BeautifulSoup(html, 'html.parser')
        root_element = soup.find(['div', 'section', 'article'])

        result = self.parser.parse_to_dict(root_element)

        assert result == expected_result
