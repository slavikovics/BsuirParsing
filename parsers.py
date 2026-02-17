import re
from bs4 import BeautifulSoup
import PyPDF2
from docx import Document
from io import BytesIO

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