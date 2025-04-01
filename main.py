import subprocess
from urllib.parse import urljoin

import requests
import re
import os
import uuid
from bs4 import BeautifulSoup
import PyPDF2
from docx import Document
from io import BytesIO
import tempfile

base_url: str = "https://www.bsuir.by/"
file_save_directory = "content_from_website"
checked_urls = set()
unchecked_urls = set()


# Downloading the page and finding all connected pages
def download_webpage(current_url):

    resp = requests.get(url=current_url)
    if resp.status_code != 200: return
    write_to_file(resp)
    find_all_links(resp.text, current_url)
    checked_urls.add(current_url)
    print(f"Downloaded from: {current_url}. In queue: {len(unchecked_urls)}. Completed: {len(checked_urls)}")


# Parsing text with html parser and writing it's content to file_save_directory
def write_to_file(resp):
    content_type = resp.headers.get('Content-Type', '')

    if resp.url.endswith('.pdf') or resp.url.endswith('.PDF'):
        parsed_text = parse_pdf(resp)

    elif resp.url.endswith('.doc') or resp.url.endswith('.DOC'):
        return

    elif resp.url.endswith('.docx') or resp.url.endswith('.DOCX'):
        parsed_text = parse_docx(resp)

    elif 'text/html' in content_type:
        parsed_text = parse_html_complicated(resp)

    else:
        return

    file_name = f"{uuid.uuid4()}.txt"
    file_path = os.path.join(file_save_directory, file_name)

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(parsed_text)


def parse_html(resp):

    soup = BeautifulSoup(resp.text, 'html.parser')
    parsed_text = soup.get_text(strip=False).replace('\n', ' ')
    return parsed_text


def parse_html_complicated(resp):
    soup = BeautifulSoup(resp.text, 'html.parser')
    content_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'div', 'strong']
    excluded_tags = ['button', 'nav', 'header', 'footer']
    content_text = []

    for tag in soup.find_all(content_tags):
        if not any(parent.name in excluded_tags for parent in tag.parents):
            content_text.append(tag.get_text(strip=False))

    result = '\n'.join(content_text)
    return re.sub(r'\s+', ' ', result)


def parse_pdf(resp):

    file = BytesIO(resp.content)
    reader = PyPDF2.PdfReader(file)
    parsed_text = ''
    for page in reader.pages:
        parsed_text += page.extract_text() + '\n'

    return parsed_text


def parse_docx(resp):

    file = BytesIO(resp.content)

    document = Document(file)
    parsed_text = ''

    for paragraph in document.paragraphs:
        parsed_text += paragraph.text

    return parsed_text


def parse_doc(resp):

    # TODO maybe use c# Aspose.Words and launch it as a process
    return


# Finding all relative links inside href="" attributes
def find_all_relative_links(resp_text, current_url):

    pattern = 'href=\"([^\"]+)\"'
    links = re.findall(pattern, resp_text)
    result = []

    for link in links:
        if str(link).find('http') == -1:
            full_url = urljoin(current_url, link)
            real_url = url_before_arguments(full_url)
            result.append(real_url)

    return result


# Finding all links which start with 'https://'
def find_all_absolute_links(resp_text):

    pattern = "http[s]?://[^\s\"'<>]+"
    links = re.findall(pattern, resp_text)

    result = []

    for link in links:
        real_url = url_before_arguments(link)
        result.append(real_url)

    return result


# To delete from the url part with arguments or anchor
def url_before_arguments(url_with_arguments):

    question_mark_index = str(url_with_arguments).find('?')
    if question_mark_index != -1: return str(url_with_arguments)[:question_mark_index]

    anchor_index = str(url_with_arguments).find('#')
    if anchor_index != -1: return str(url_with_arguments)[:anchor_index]

    return url_with_arguments


# Finding all links in resp_text. Adding new urls into unchecked_urls
def find_all_links(resp_text, current_url):

    links = find_all_relative_links(resp_text, current_url)
    links.extend(find_all_absolute_links(resp_text))

    for link in links:
        if str(link).find(".css") != -1: continue
        if str(link).find(".js") != -1: continue
        if any(ext in str(link) for ext in [".png", ".jpg", ".doc", ".rss", ".RTF", ".ico"]):
            continue
        if str(link).find("https://bsuir.by") == -1 and str(link).find("https://www.bsuir.by") == -1: continue
        if link not in checked_urls: unchecked_urls.add(link) # and not in unchecked_urls


unchecked_urls.add(base_url)
while len(unchecked_urls) != 0:
    try:
        current_url = unchecked_urls.pop()
        download_webpage(current_url)
    except Exception as e:
        print(f"Error occurred: {e}. Error in: {current_url}")

print("Checked urls:")
for url in checked_urls:
    print(f"Url: {url}")