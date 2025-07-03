# Example HTML snippet covering various heading scenarios
TEST_HTML = '''
<section id="root">
    <h1>Main Title</h1>
    <p>This is the introduction paragraph, explaining the document purpose.</p>
    <h2>Section One</h2>
    <p>Details of section one.</p>
    <h2>Section Two</h2>
    <p>Details of section two.</p>
    <div role="heading" aria-level="3">ARIA Heading Level 3 as a child of node 2</div>
    <p>Content under ARIA heading as well as the h2 tag.</p>
    <div role="heading" aria-level="3">2nd ARIA Heading Level 3 as a child of node 2</div>
    <p>Content under ARIA heading as well as the h2 tag.</p>
    <section id="wrapped">
        <h2>Already Wrapped Section</h2>
        <p>Pre-wrapped content should not get double-wrapping.</p>
        <div role="heading" aria-level="3">ARIA Heading inside wrapped</div>
        <p>More details in wrapped section.</p>
    </section>
    <div role="heading" aria-level="2">ARIA Heading Level 2</div>
    <p>Content under ARIA heading level 2.</p>
</section>
'''


from bs4 import BeautifulSoup, Tag


def get_heading_level(tag: Tag) -> int:
    """
    Normalize a tag to a heading level:
      - h1-h6 → 1-6
      - any tag with aria-level attribute
      - any tag with role="heading" defaults to aria-level or 2
    Lower number → higher-level heading.
    """
    if not isinstance(tag, Tag):
        return None
    if tag.has_attr('aria-level'):
        try:
            return int(tag['aria-level'])
        except (ValueError, TypeError):
            pass
    if tag.name and tag.name.startswith('h') and len(tag.name) == 2 and tag.name[1].isdigit():
        return int(tag.name[1])
    if tag.get('role') == 'heading':
        return int(tag.get('aria-level', 2))
    return None


def find_highest_heading(root: Tag) -> Tag:
    """
    Return the direct or nested tag with the smallest heading level.
    """
    headings = [(get_heading_level(t), t) for t in root.find_all(lambda t: get_heading_level(t) is not None)]
    if not headings:
        return None
    _, tag = min(headings, key=lambda x: x[0])
    return tag


def chunk_section(root: Tag) -> list:
    """
    Top-down split of `root` into a list of nodes.
    Each node is a dict:
      - title: the section heading
      - text: HTML of the section plus summaries of its immediate children
      - summary: text of the first <p> in the section

    Returns a flat list of nodes (parent before children).
    """
    # 1) Identify this section's title and summary
    title_tag = find_highest_heading(root)
    title = title_tag.get_text(strip=True) if title_tag else 'Untitled'

    # Find direct children of root (skip strings)
    children = [c for c in root.children if not (getattr(c, 'name', None) is None and not str(c).strip())]

    # Locate title index among children
    title_idx = next((i for i,c in enumerate(children) if c is title_tag), 0)
    # Locate summary paragraph index after title
    summary_idx = title_idx
    for i in range(title_idx+1, len(children)):
        c = children[i]
        if isinstance(c, Tag) and c.name == 'p':
            summary_idx = i
            break
    # Build this node's own text (title + its own summary)
    root_text_elems = children[:summary_idx+1]
    node_text = ''.join(str(x) for x in root_text_elems)
    summary = ''
    if summary_idx > title_idx and isinstance(children[summary_idx], Tag) and children[summary_idx].name == 'p':
        summary = children[summary_idx].get_text(strip=True)

    # 2) Split remaining children into segments
    segments = []
    current = []
    # next heading level to split on
    base_level = get_heading_level(title_tag) or 0
    split_level = base_level + 1

    for child in children[summary_idx+1:]:
        # explicit <section> always splits
        if isinstance(child, Tag) and child.name == 'section':
            if current:
                segments.append(current)
            segments.append([child])
            current = []
            continue
        # any heading at level==split_level splits
        lvl = get_heading_level(child)
        if isinstance(child, Tag) and lvl == split_level:
            if current:
                segments.append(current)
            current = [child]
            continue
        # else, group with current
        current.append(child)
    if current:
        segments.append(current)

    # 3) Create this node + recurse into segments
    nodes = []
    # placeholder for children summaries
    child_summaries = []

    # Collect child nodes
    all_child_nodes = []
    for seg in segments:
        # Wrap this segment into a temporary <section>
        if len(seg)==1 and isinstance(seg[0], Tag) and seg[0].name=='section':
            seg_root = seg[0]
        else:
            seg_wrapper = BeautifulSoup('<section></section>', 'html.parser').section
            for el in seg:
                seg_wrapper.append(el)
            seg_root = seg_wrapper
        # Recursively chunk
        child_nodes = chunk_section(seg_root)
        all_child_nodes.extend(child_nodes)
        # For summary injection, capture the immediate child summary (first child in that chunk)
        first_child = child_nodes[0]
        child_summaries.append((first_child['title'], first_child.get('summary','')))

    # Inject summaries of immediate children into this node's text
    if child_summaries:
        node_text += '<ul>'
        for t, s in child_summaries:
            node_text += f'<li><strong>{t}:</strong> {s}</li>'
        node_text += '</ul>'

    # Build this node
    node = {'title': title, 'text': node_text, 'summary': summary}
    nodes.append(node)
    # Append all descendants
    nodes.extend(all_child_nodes)
    return nodes


if __name__ == '__main__':
    soup = BeautifulSoup(test_html, 'html.parser')
    root = soup.find('section', {'id': 'root'})
    nodes = chunk_section(root)
    for nd in nodes:
        print(f"--- Node: {nd['title']} ---")
        print(nd['text'], '\n')
        if nd['summary']:
            print("Summary:", nd['summary'], '\n')
