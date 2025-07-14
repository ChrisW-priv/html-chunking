"""
HTML Section Parser - Extracts hierarchical sections from HTML content
"""

from bs4 import BeautifulSoup
from bs4.element import Tag
from typing import Dict, List, Any, Optional


class HTMLSectionParser:
    """Fast parser for HTML that finds sections and splits content into subsections."""

    def __init__(self):
        self.heading_tags = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}

    def get_heading_level(self, element) -> Optional[int]:
        """Extract heading level from an element."""
        # Standard heading tags
        if element.name in self.heading_tags:
            return int(element.name[1])

        # Elements with role="heading" and aria-level
        if element.get('role') == 'heading':
            aria_level = element.get('aria-level')
            if aria_level and aria_level.isdigit():
                return int(aria_level)
            # Default to level 1 if no aria-level specified
            return 1

        # Elements with aria-level (even without role="heading")
        aria_level = element.get('aria-level')
        if aria_level and aria_level.isdigit():
            return int(aria_level)

        return None

    def extract_text_between_headings(self, soup, start_element, end_element=None) -> str:
        """Extract all content between two heading elements."""
        content_parts = []
        current = start_element.next_sibling

        while current and current != end_element:
            if isinstance(current, Tag):
                # Check if this is a heading element
                if current.name in self.heading_tags or \
                   (current.get('role') == 'heading') or \
                   (current.get('aria-level') and current.get('aria-level').isdigit()):
                    # Hit another heading, stop
                    break

                # Check if this element contains headings (like a section)
                nested_headings = self._find_headings_in_element(current)
                if nested_headings:
                    # This element contains headings, so we should stop here
                    # and let those headings be processed as subsections
                    break

                content_parts.append(str(current))
            elif hasattr(current, 'string') and current.string and current.string.strip():
                # It's text content
                content_parts.append(current.string)
            current = current.next_sibling

        return ''.join(content_parts).strip()

    def _find_headings_in_element(self, element):
        """Find all heading elements within a given element."""
        headings = []
        for child in element.find_all():
            level = self.get_heading_level(child)
            if level is not None:
                headings.append((child, level))
        return headings

    def find_next_heading_at_level_or_higher(self, soup, start_element, current_level: int):
        """Find the next heading at the same level or higher."""
        current = start_element.next_sibling

        while current:
            if isinstance(current, Tag):
                level = self.get_heading_level(current)
                if level is not None and level <= current_level:
                    return current
            current = current.next_sibling

        return None

    def parse_sections(self, html_content: str) -> List[Dict[str, Any]]:
        """Parse HTML and extract hierarchical sections."""
        soup = BeautifulSoup(html_content, 'lxml')

        # Find all potential heading elements in document order
        headings = []
        for element in soup.find_all():
            level = self.get_heading_level(element)
            if level is not None:
                headings.append((element, level))

        if not headings:
            return []

        result = self._build_hierarchy(soup, headings)

        # If there's only one top-level section and the test expects a single object
        # (not a list), we might need to adjust this based on the specific use case
        return result

    def _build_hierarchy(self, soup, headings: List[tuple]) -> List[Dict[str, Any]]:
        """Build hierarchical structure from headings."""
        if not headings:
            return []

        result = []
        i = 0

        while i < len(headings):
            current_element, current_level = headings[i]

            # Find all headings that belong to this section (higher level numbers)
            subsection_headings = []
            j = i + 1

            # Collect all subsections until we hit a heading at same or higher level
            while j < len(headings):
                next_element, next_level = headings[j]
                if next_level <= current_level:
                    break
                subsection_headings.append(headings[j])
                j += 1

            # Extract text content for this section
            # Find the next heading at the same or higher level for boundary
            next_boundary = None
            if j < len(headings):
                next_boundary = headings[j][0]

            text_content = self.extract_text_between_headings(
                soup, current_element, next_boundary
            )

            # Build subsections recursively
            subsections = self._build_hierarchy(soup, subsection_headings)

            # Build the section dictionary
            section = {
                'title': current_element.get_text().strip(),
                'text': text_content,
                'level': current_level,
                'subsections': subsections
            }

            result.append(section)

            # Move to the next section at the same or higher level
            i = j

        return result
