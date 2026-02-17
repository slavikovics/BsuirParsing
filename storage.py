import os
import uuid
import config
import parsers

def write_to_file_sync(content: bytes, headers, url: str):
    content_type = headers.get('Content-Type', '')
    parsed_text = None

    if url.endswith('.pdf') or url.endswith('.PDF'):
        parsed_text = parsers.parse_pdf(content)
    elif url.endswith('.doc') or url.endswith('.DOC'):
        return                      # .doc not supported
    elif url.endswith('.docx') or url.endswith('.DOCX'):
        parsed_text = parsers.parse_docx(content)
    elif 'text/html' in content_type:
        parsed_text = parsers.parse_html_complicated(content)
    else:
        return

    os.makedirs(config.FILE_SAVE_DIRECTORY, exist_ok=True)

    file_name = f"{uuid.uuid4()}.txt"
    file_path = os.path.join(config.FILE_SAVE_DIRECTORY, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(parsed_text)