from bs4 import BeautifulSoup, Tag
import copy

# ——— Helpers ———

def get_heading_level(tag: Tag) -> int:
    if not isinstance(tag, Tag):
        return None
    if tag.has_attr('aria-level'):
        try:
            return int(tag['aria-level'])
        except:
            pass
    if tag.name and tag.name.startswith('h') and tag.name[1:].isdigit():
        return int(tag.name[1])
    if tag.get('role') == 'heading':
        return int(tag.get('aria-level', 2))
    return None


def find_title_tag(root: Tag) -> Tag:
    hs = [t for t in root.find_all(lambda t: get_heading_level(t) is not None)]
    return min(hs, key=get_heading_level) if hs else None


def extract_summary(children, title_idx):
    # Collect up to two non-empty <p> tags after the title
    summary_nodes = []
    last_idx = title_idx
    for i, c in enumerate(children[title_idx+1:], start=title_idx+1):
        if isinstance(c, Tag) and c.name == 'p' and c.get_text(strip=True):
            summary_nodes.append(c)
            last_idx = i
            if len(summary_nodes) == 2:
                break
    return ''.join(n.prettify() for n in summary_nodes), last_idx


def split_segments(children, base_level):
    out, curr = [], []
    split_lvl = base_level + 1
    for c in children:
        lvl = get_heading_level(c)
        if isinstance(c, Tag) and c.name == 'section':
            if curr: out.append(curr); curr = []
            out.append([c])
        elif lvl == split_lvl or lvl is not None and lvl > split_lvl:
            if curr: out.append(curr)
            curr = [c]
        else:
            curr.append(c)
    if curr:
        out.append(curr)
    return out


def wrap_if_needed(seg):
    if len(seg) == 1 and isinstance(seg[0], Tag) and seg[0].name == 'section':
        return seg[0]
    wrapper = BeautifulSoup('<section></section>', 'html.parser').section
    for el in seg:
        wrapper.append(el)
    return wrapper

# ——— Main chunker ———

def chunk_section(root: Tag) -> list:
    title_tag = find_title_tag(root)
    title = title_tag.get_text(strip=True) if title_tag else 'Untitled'
    children = [c for c in root.children if not (isinstance(c, str) and not c.strip())]
    title_idx = children.index(title_tag) if title_tag in children else -1

    # extract summary safely
    summary, summary_idx = extract_summary(children, title_idx)

    # build initial node_text up through summary
    node_text = ''.join(str(x) for x in children[:summary_idx+1])

    # split into child segments
    base_lvl = get_heading_level(title_tag) or 0
    segments = split_segments(children[summary_idx+1:], base_lvl)

    # gather child summaries with fallback
    child_summaries = []
    for seg in segments:
        seg_root = wrap_if_needed(seg)
        ct = find_title_tag(seg_root)
        # fallback: use first heading element in segment
        if ct:
            child_title = ct.get_text(strip=True)
        else:
            next_hd = next((c for c in seg if isinstance(c, Tag) and get_heading_level(c) is not None), None)
            child_title = next_hd.get_text(strip=True) if next_hd else 'Untitled'
        ps = seg_root.find('p')
        if ps and ps.get_text(strip=True):
            snippet = ps.get_text(strip=True)
        else:
            snippet = child_title
        child_summaries.append((child_title, snippet))

    if child_summaries:
        node_text += '<ul>'
        for ct, cs in child_summaries:
            node_text += f'<li><strong>{ct}</strong><p>{cs}</p></li>'
        node_text += '</ul>'

    # assemble this node + recurse
    nodes = [{'title': title, 'text': node_text, 'summary': summary}]
    for seg in segments:
        nodes.extend(chunk_section(wrap_if_needed(seg)))
    return nodes

# ——— Example run ———

if __name__ == '__main__':
    TEST_HTML = '''
    <section id="root">
        <h1>Main Title</h1>
        <p>Introduction paragraph.</p>

        <h2>Section A</h2>
        <p> Content A.</p>

        <h2>Section B</h2>
        <div role="heading" aria-level="3">Subheading B.1</div>
        <p>Deep content B.1.</p>

        <section>
            <h2>Section C</h2>
            <p>Content C.</p>
        </section>

        <h6 aria-level="7">Deep Section</h6>
        <p>Deep content.</p>
        <h6 aria-level="8">Deep nested Section</h6>
        <p>Deep nested content.</p>
    </section>
    '''
    soup = BeautifulSoup(TEST_HTML, 'html.parser')
    root = soup.find('section', {'id': 'root'})
    nodes = chunk_section(root)
    for n in nodes:
        print(n)

