from chunk_base import Chunk

class TextChunk(Chunk):

    def __init__(self, id: str, source_url: str, xpath: str, content: str):
        super().__init__(id=id, source_url=source_url, xpath=xpath, content=content)

    def __str__(self):
        return self.content
