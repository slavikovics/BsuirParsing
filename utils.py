import re
from urllib.parse import urljoin, urlparse

def get_parent_domain_from_url(url):
    """Extract the parent domain (e.g., example.com from sub.example.com)."""
    parsed = urlparse(url)
    netloc = parsed.netloc
    if ':' in netloc:
        netloc = netloc.split(':')[0]
    parts = netloc.split('.')
    if len(parts) > 2:
        return '.'.join(parts[1:])
    return netloc

def url_before_arguments(url: str):
    q_idx = url.find('?')
    if q_idx != -1:
        return url[:q_idx]
    a_idx = url.find('#')
    if a_idx != -1:
        return url[:a_idx]
    return url

def find_all_relative_links(html_text: str, current_url: str):
    pattern = 'href="([^"]+)"'
    links = re.findall(pattern, html_text)
    result = []
    for link in links:
        if not link.startswith('http'):
            full_url = urljoin(current_url, link)
            result.append(full_url)
    return result

def find_all_absolute_links(html_text: str):
    pattern = r"https?://[^\s\"'<>]+"
    return re.findall(pattern, html_text)

def find_all_links(html_text: str, current_url: str, only_html: bool = False):
    """Extract absolute links from HTML, filtered by same parent domain."""
    relative = find_all_relative_links(html_text, current_url)
    absolute = find_all_absolute_links(html_text)
    links = relative + absolute

    allowed_domain = get_parent_domain_from_url(current_url)

    filtered = []
    for link in links:
        if any(ext in link for ext in [".css", ".js", ".png", ".jpg", ".doc", ".rss", ".RTF", ".ico"]):
            continue
        if only_html and any(ext in link for ext in [".pdf", ".doc", ".docx", ".PDF", ".DOC", ".DOCX"]):
            continue
        link_domain = get_parent_domain_from_url(link)
        if link_domain != allowed_domain:
            continue
        cleaned = url_before_arguments(link)
        filtered.append(cleaned)
    return filtered