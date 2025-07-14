from typing import Generator
from bs4 import BeautifulSoup
import copy


def find_root_element(soup):
    """Find the most appropriate root element in the soup."""
    for tag in ['main', 'article']:
        element = soup.find(tag)
        if element and element.get_text().strip():
            return element

    body = soup.find('body')
    if body and body.get_text().strip():
        return body

    section = soup.find('section')
    if section and section.get_text().strip():
        return section

    for div in soup.find_all('div'):
        if len(div.get_text().strip()) > 100:  # Substantial content
            return div

    return soup


class SectionParser:
    """Reference implementation of the section parser for testing."""

    def __init__(self):
        self.heading_aria_levels = {
            'h1': 1, 'h2': 2, 'h3': 3, 'h4': 4, 'h5': 5, 'h6': 6
        }

    def parse_html(self, html: str) -> dict:
        """Parse HTML string into JSON object."""
        soup = BeautifulSoup(html, 'lxml')
        root_element = find_root_element(soup)

        # Extract structured content
        result = self.parse_to_dict(root_element)
        return result

    def get_aria_level(self, element) -> int | None:
        """Get the aria level of an element."""
        if element.name in self.heading_aria_levels:
            # Check for aria-level override, like for h6 with aria-level="7"
            aria_level = element.get('aria-level')
            if aria_level:
                try:
                    return int(aria_level)
                except ValueError:
                    return self.heading_aria_levels[element.name]
            return self.heading_aria_levels[element.name]

        # Check for div with role="heading" and aria-level
        if element.name == 'div' and element.get('role') == 'heading':
            aria_level = element.get('aria-level')
            if aria_level:
                try:
                    return int(aria_level)
                except ValueError:
                    return None

        return None  # Not a heading

    def is_heading(self, element) -> bool:
        """Check if element is a heading."""
        return self.get_aria_level(element) is not None

    def extract_text_content(self, element) -> str:
        """Extract text content from p tags and other text elements."""
        text_elements = []

        for child in element.children:
            if hasattr(child, 'name'):
                if child.name == 'p':
                    text_elements.append(child.get_text().strip())
                elif child.name in ['ul', 'ol', 'blockquote', 'div'] and not self.is_heading(child):
                    text_elements.append(child.get_text().strip())

        return '\n'.join(text_elements).strip()

    def should_include_element(self, element) -> bool:
        """Determine if an element should be included in the text field.

        Default to inclusion, only exclude clearly irrelevant parts.
        """
        # Skip heading elements - they're handled separately
        if self.is_heading(element):
            return False

        # Skip script and style tags - never want these
        if element.name in ['script', 'style', 'noscript']:
            return False

        # Skip meta elements and other head content
        if element.name in ['meta', 'link', 'title', 'base']:
            return False

        # Skip empty elements with no meaningful content
        if not element.get_text().strip():
            return False

        # Skip elements that contain headings - they'll be processed as subsections
        if any(self.is_heading(child) for child in element.find_all() if hasattr(child, 'name')):
            return False

        # Default: include everything else
        return True

    def extract_html_content(self, element) -> str:
        """Extract HTML content preserving structure, excluding headings and irrelevant elements."""
        content_elements = []

        for child in element.children:
            if hasattr(child, 'name'):
                if self.should_include_element(child):
                    content_elements.append(str(child))
            elif hasattr(child, 'strip') and child.strip():
                # Include direct text content
                content_elements.append(child.strip())

        return '\n'.join(content_elements).strip()

    def get_section_content(self, start_element, siblings) -> list:
        """Get content between current heading and next heading of same or higher level."""
        current_level = self.get_aria_level(start_element) or float('inf')
        content = []

        # Start collecting from the element after the heading
        collecting = False

        for sibling in siblings:
            if sibling == start_element:
                collecting = True
                continue

            if collecting:
                if hasattr(sibling, 'name') and self.is_heading(sibling):
                    sibling_level = self.get_aria_level(sibling) or float('inf')
                    if sibling_level <= current_level:
                        # Found a heading at same or higher level, stop collecting
                        break

                content.append(sibling)

        return content

    def is_already_wrapped_in_section(self, element) -> bool:
        """Check if element is already wrapped in a section tag."""
        parent = element.parent
        while parent:
            if parent.name == 'section':
                return True
            parent = parent.parent
        return False

    def create_section_wrapper(self, heading, content_elements) -> BeautifulSoup:
        """Create a new section wrapper with heading and content."""
        soup = BeautifulSoup('<section></section>', 'lxml')
        section = soup.find('section')

        # Add heading
        section.append(heading.extract())

        # Add content elements
        for element in content_elements:
            if hasattr(element, 'extract'):
                section.append(element.extract())

        return section

    def find_highest_aria_element(self, root_element):
        """Find the highest aria element (lowest aria-level number)."""
        headings = []

        for element in root_element.find_all():
            if self.is_heading(element):
                headings.append((element, self.get_aria_level(element)))

        if not headings:
            return None

        # Sort by aria level (lowest first)
        headings.sort(key=lambda x: x[1])
        return headings[0][0]

    def get_all_headings_at_level(self, root_element, level: int) -> Generator:
        """Get all headings at a specific aria level."""
        for element in root_element.find_all():
            if self.is_heading(element) and (self.get_aria_level(element) or float('inf')) == level:
                yield element

    def is_base_case(self, element) -> bool:
        """Check if this is a base case (container with single heading + text, no nested headings)."""
        # If element is a heading, use old behavior
        if self.is_heading(element):
            current_level = self.get_aria_level(element)
            if current_level is None:
                return True

            # Check if there are any sibling headings with deeper levels that come after this element
            parent = element.parent
            if not parent:
                return True

            found_current = False
            for sibling in parent.children:
                if hasattr(sibling, 'name'):
                    if sibling == element:
                        found_current = True
                        continue

                    if found_current and self.is_heading(sibling):
                        sibling_level = self.get_aria_level(sibling) or float('inf')
                        if sibling_level > current_level:
                            return False
                        elif sibling_level <= current_level:
                            # Found a heading at same or higher level, this section ends
                            break

            return True

        # If element is a container, check if it contains only one heading
        heading_count = 0
        for child in element.find_all():
            if self.is_heading(child):
                heading_count += 1
                if heading_count > 1:
                    return False

        return heading_count == 1

    def parse_section(self, root_element):
        """Parse a section and wrap subsections appropriately."""
        # Find the highest aria element
        highest_element = self.find_highest_aria_element(root_element)
        if not highest_element:
            return root_element

        highest_level = self.get_aria_level(highest_element)
        if highest_level is None:
            return root_element

        # Find all elements at the next level down
        next_level_headings = []

        # Look for headings at next level
        for element in root_element.find_all():
            if self.is_heading(element):
                elem_level = self.get_aria_level(element)
                if elem_level in range(highest_level, highest_level+2):
                    next_level_headings.append(element)

        # Process each heading at the next level
        for heading in next_level_headings:
            if self.is_already_wrapped_in_section(heading):
                continue  # Skip already wrapped sections

            # Get siblings for content extraction
            siblings = list(heading.parent.children)
            content = self.get_section_content(heading, siblings)

            # Create section wrapper
            section = self.create_section_wrapper(heading, content)

            # Insert the section where the heading was
            if heading.parent:
                heading.parent.insert(0, section)

        return root_element

    def parse_to_dict(self, root_element) -> dict:
        """Parse a section and return structured data as dictionaries."""
        # Base case: if this is a simple section with one heading
        if self.is_base_case(root_element):
            # Find the single heading
            heading = None
            for element in root_element.find_all():
                if self.is_heading(element):
                    heading = element
                    break

            if heading:
                title = heading.get_text().strip()
                text = self.extract_html_content(root_element)
                return {
                    'title': title,
                    'text': text,
                    'level': self.get_aria_level(heading),
                    'subsections': []
                }
            else:
                # No heading found, return text only
                return {
                    'title': '',
                    'text': self.extract_html_content(root_element),
                    'level': None,
                    'subsections': []
                }

        # Complex case: multiple headings, need to create nested structure
        highest_element = self.find_highest_aria_element(root_element)
        if not highest_element:
            return {
                'title': '',
                'text': self.extract_html_content(root_element),
                'level': None,
                'subsections': []
            }

        highest_level = self.get_aria_level(highest_element)
        title = highest_element.get_text().strip()

        # Find direct subsections - headings that should be processed at this level
        next_level_headings = []
        processed_elements = set()

        # Get all elements in document order
        all_elements = list(root_element.find_all())

        # Find position of highest element
        highest_pos = all_elements.index(highest_element)

        # Look for headings that come after the highest element
        # but only include those that are direct subsections
        i = highest_pos + 1
        while i < len(all_elements):
            element = all_elements[i]

            # Skip elements that have already been processed
            if id(element) in processed_elements:
                i += 1
                continue

            if self.is_heading(element):
                elem_level = self.get_aria_level(element)
                if elem_level and elem_level >= highest_level:
                    # Check if this heading is the next level down (direct subsection)
                    # or if it's nested deeper within another subsection
                    is_direct_subsection = True

                    # Look for any heading between highest_element and current element
                    # that has a level between highest_level and elem_level
                    for j in range(highest_pos + 1, i):
                        intermediate_elem = all_elements[j]
                        if (self.is_heading(intermediate_elem) and
                            id(intermediate_elem) not in processed_elements):
                            intermediate_level = self.get_aria_level(intermediate_elem)
                            if (intermediate_level and
                                highest_level <= intermediate_level <= elem_level):
                                # This element is nested within an intermediate heading
                                is_direct_subsection = False
                                break

                    if is_direct_subsection:
                        next_level_headings.append(element)
                        processed_elements.add(id(element))

                        # Mark all content elements of this subsection as processed
                        siblings = list(element.parent.children)
                        content = self.get_section_content(element, siblings)
                        for content_elem in content:
                            if hasattr(content_elem, 'name'):
                                processed_elements.add(id(content_elem))
                                # Also mark all descendants as processed
                                if hasattr(content_elem, 'find_all'):
                                    for descendant in content_elem.find_all():
                                        processed_elements.add(id(descendant))

                elif elem_level and elem_level <= highest_level:
                    # We've reached a heading at same or higher level, stop looking
                    break

            i += 1

        # Extract HTML content that comes before any subsections
        text_content = []
        found_first_subsection = False

        for child in root_element.children:
            if hasattr(child, 'name'):
                if child == highest_element:
                    continue
                elif self.is_heading(child) and self.get_aria_level(child) and self.get_aria_level(child) > highest_level:
                    found_first_subsection = True
                    break
                elif not found_first_subsection:
                    if self.should_include_element(child):
                        text_content.append(str(child))
            elif hasattr(child, 'strip') and child.strip() and not found_first_subsection:
                # Include direct text content
                text_content.append(child.strip())

        # Create subsections
        subsections = []
        for heading in next_level_headings:
            # Get content for this subsection
            siblings = list(heading.parent.children)
            content = self.get_section_content(heading, siblings)

            # Create a temporary container for this subsection
            temp_soup = BeautifulSoup('<div></div>', 'lxml')
            temp_div = temp_soup.find('div')

            # Clone the heading instead of extracting to avoid modifying original
            heading_copy = copy.deepcopy(heading)
            heading_element = heading_copy.find()
            if heading_element:
                temp_div.append(heading_element)

            for element in content:
                if hasattr(element, 'name'):
                    # Clone the element instead of extracting
                    element_soup = BeautifulSoup(str(element), 'lxml')
                    element_copy = element_soup.find()
                    if element_copy:
                        temp_div.append(element_copy)

            # Recursively parse this subsection
            subsection_data = self.parse_to_dict(temp_div)
            subsections.append(subsection_data)

        return {
            'title': title,
            'text': '\n'.join(text_content).strip(),
            'level': highest_level,
            'subsections': subsections
        }
