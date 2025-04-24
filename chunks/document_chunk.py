from chunk_base import Chunk

class DocumentChunk(Chunk):

    def __init__(self, id: str, source_url: str, xpath: str, document_label: str, document_url: str):
        super().__init__(id=id, source_url=source_url, xpath=xpath, content=document_label)
        self.documet_url = document_url

    def __str__(self):
        return None