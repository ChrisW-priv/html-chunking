import pytest
from bs4 import BeautifulSoup
from content_extraction.semantic_chunk_html import SectionParser


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
            'text': '<p>Article content with <cite>citation</cite> and <q>quoted text</q>.</p>',
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
            'text': '<p>Article content with <strong>formatting</strong>.</p>',
            'level': 1,
            'subsections': []
        }),
    ])
    def test_parse_to_dict(self, html, expected_result):
        """Test the full parse_to_dict functionality with various scenarios."""
        result = self.parser.parse_html(html)

        assert result == expected_result
