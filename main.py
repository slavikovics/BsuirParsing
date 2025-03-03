from urllib.parse import urljoin

import requests
import re
import os
import uuid
from bs4 import BeautifulSoup
import PyPDF2
import pypandoc
from docx import Document
from io import BytesIO

base_url: str = "https://www.bsuir.by/"
file_save_directory = "content_from_website"
checked_urls = set()
unchecked_urls = set()


# Downloading the page and finding all connected pages
def download_webpage():

    current_url = unchecked_urls.pop()
    resp = requests.get(url=current_url)
    if resp.status_code != 200: return
    write_to_file(resp)
    find_all_links(resp.text, current_url)
    checked_urls.add(current_url)
    print(f"Downloaded from: {current_url}.")


# Parsing text with html parser and writing it's content to file_save_directory
def write_to_file(resp):

    if resp.url.endswith('.pdf') or resp.url.endswith('.PDF'):
        parsed_text = parse_pdf(resp)

    elif resp.url.endswith('.doc') or resp.url.endswith('.DOC'):
        parsed_text = parse_doc(resp)

    elif resp.url.endswith('.docx') or resp.url.endswith('.DOCX'):
        parsed_text = parse_docx(resp)

    else:
        parsed_text = parse_html(resp)

    file_name = f"{uuid.uuid4()}.txt"
    file_path = os.path.join(file_save_directory, file_name)

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(parsed_text)


def parse_html(resp):

    soup = BeautifulSoup(resp.text, 'html.parser')
    parsed_text = soup.get_text(strip=False).replace('\n', ' ')
    return parsed_text


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

    file = BytesIO(resp.content)
    parsed_text = pypandoc.convert_file(file, 'plain')

    return parsed_text


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
        if str(link).find("https://bsuir.by") == -1 and str(link).find("https://www.bsuir.by") == -1: continue
        if link not in checked_urls: unchecked_urls.add(link)


unchecked_urls.add(base_url)
while len(unchecked_urls) != 0:
    try:
        download_webpage()
    except Exception as e:
        print(f"Error occurred: {e}")

print("Checked urls:")
for url in checked_urls:
    print(f"Url: {url}")