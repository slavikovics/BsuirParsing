import asyncio
import aiohttp
import re
import os
import uuid
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import PyPDF2
from docx import Document
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

SEED_FILE = os.getenv('SEED_FILE', 'seeds.txt')
NUM_WORKERS = int(os.getenv('NUM_WORKERS', '5'))
file_save_directory = "content_from_website"
max_concurrent_requests = int(os.getenv('MAX_CONCURRENT_REQUESTS', '10'))
user_agent = "Mozilla/5.0 (compatible; AsyncCrawler/1.0)"

checked_urls = set()
seen_urls = set()
seen_lock = asyncio.Lock()

def get_parent_domain_from_url(url):
    """Extract the parent domain (e.g., example.com from sub.example.com) from a URL."""
    parsed = urlparse(url)
    netloc = parsed.netloc
    if ':' in netloc:                # remove port if present
        netloc = netloc.split(':')[0]
    parts = netloc.split('.')
    if len(parts) > 2:
        return '.'.join(parts[1:])
    return netloc

def write_to_file_sync(content: bytes, headers, url: str):
    content_type = headers.get('Content-Type', '')
    parsed_text = None

    if url.endswith('.pdf') or url.endswith('.PDF'):
        parsed_text = parse_pdf(content)
    elif url.endswith('.doc') or url.endswith('.DOC'):
        return  # .doc not supported yet
    elif url.endswith('.docx') or url.endswith('.DOCX'):
        parsed_text = parse_docx(content)
    elif 'text/html' in content_type:
        parsed_text = parse_html_complicated(content)
    else:
        return

    os.makedirs(file_save_directory, exist_ok=True)

    file_name = f"{uuid.uuid4()}.txt"
    file_path = os.path.join(file_save_directory, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(parsed_text)

def parse_html_complicated(html_content: bytes):
    soup = BeautifulSoup(html_content, 'html.parser')
    content_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'div', 'strong']
    excluded_tags = ['button', 'nav', 'header', 'footer']
    content_text = []
    for tag in soup.find_all(content_tags):
        if not any(parent.name in excluded_tags for parent in tag.parents):
            content_text.append(tag.get_text(strip=False))
    result = '\n'.join(content_text)
    return re.sub(r'\s+', ' ', result)

def parse_pdf(pdf_content: bytes):
    file = BytesIO(pdf_content)
    reader = PyPDF2.PdfReader(file)
    text = ''
    for page in reader.pages:
        text += page.extract_text() + '\n'
    return text

def parse_docx(docx_content: bytes):
    file = BytesIO(docx_content)
    document = Document(file)
    text = ''
    for paragraph in document.paragraphs:
        text += paragraph.text
    return text

def find_all_links(html_text: str, current_url: str, only_html: bool = False):
    """Extract all absolute links from HTML, then keep only those with the same parent domain as current_url."""
    relative = find_all_relative_links(html_text, current_url)
    absolute = find_all_absolute_links(html_text)
    links = relative + absolute

    # Get the allowed parent domain from the current page
    allowed_domain = get_parent_domain_from_url(current_url)

    filtered = []
    for link in links:
        # Skip file extensions we don't want to follow
        if any(ext in link for ext in [".css", ".js", ".png", ".jpg", ".doc", ".rss", ".RTF", ".ico"]):
            continue
        if only_html and any(ext in link for ext in [".pdf", ".doc", ".docx", ".PDF", ".DOC", ".DOCX"]):
            continue
        # Stay within the same site (parent domain)
        link_domain = get_parent_domain_from_url(link)
        if link_domain != allowed_domain:
            continue
        cleaned = url_before_arguments(link)
        filtered.append(cleaned)
    return filtered

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

def url_before_arguments(url: str):
    q_idx = url.find('?')
    if q_idx != -1:
        return url[:q_idx]
    a_idx = url.find('#')
    if a_idx != -1:
        return url[:a_idx]
    return url

async def worker(worker_id: int, session: aiohttp.ClientSession, queue: asyncio.Queue, semaphore: asyncio.Semaphore):
    print(f"Worker {worker_id} started")
    while True:
        url = await queue.get()
        if url is None:                     # shutdown signal
            queue.task_done()
            break

        print(f"Worker {worker_id} processing {url}")

        async with semaphore:
            try:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        print(f"  Worker {worker_id}: {url} returned {resp.status}")
                        queue.task_done()
                        continue

                    content = await resp.read()
                    headers = resp.headers
                    final_url = str(resp.url)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                print(f"  Worker {worker_id}: Error fetching {url}: {e}")
                queue.task_done()
                continue

        async with seen_lock:
            checked_urls.add(url)

        await asyncio.to_thread(write_to_file_sync, content, headers, final_url)

        if 'text/html' in headers.get('Content-Type', ''):
            html_text = content.decode('utf-8', errors='ignore')
            new_links = await asyncio.to_thread(find_all_links, html_text, final_url, only_html=True)

            for link in new_links:
                async with seen_lock:
                    if link not in seen_urls:
                        seen_urls.add(link)
                        await queue.put(link)

        queue.task_done()
        print(f"  Worker {worker_id}: finished {url}, queue size ≈ {queue.qsize()}")

async def main():
    os.makedirs(file_save_directory, exist_ok=True)

    # Read seed URLs from the file specified in SEED_FILE
    try:
        with open(SEED_FILE, 'r') as f:
            seeds = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: Seed file '{SEED_FILE}' not found.")
        return
    except Exception as e:
        print(f"Error reading seed file: {e}")
        return

    if not seeds:
        print("No seed URLs found in the file.")
        return

    print(f"Loaded {len(seeds)} seed URLs from '{SEED_FILE}'.")
    print(f"Using {NUM_WORKERS} workers.")

    queue = asyncio.Queue()
    for url in seeds:
        await queue.put(url)
        async with seen_lock:
            seen_urls.add(url)

    semaphore = asyncio.Semaphore(max_concurrent_requests)

    connector = aiohttp.TCPConnector(limit=0)
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        headers={'User-Agent': user_agent}
    ) as session:

        workers = [asyncio.create_task(worker(i, session, queue, semaphore)) for i in range(NUM_WORKERS)]

        await queue.join()

        for _ in workers:
            await queue.put(None)
        await asyncio.gather(*workers, return_exceptions=True)

    print("\nCrawling finished.")
    print(f"Checked URLs: {len(checked_urls)}")

if __name__ == "__main__":
    asyncio.run(main())