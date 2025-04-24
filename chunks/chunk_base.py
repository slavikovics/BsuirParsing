class Chunk:

    def __init__(self, id: str, source_url: str, xpath: str = None, children: list = None, content: str = None):
        self.id = id
        self.source_url = source_url
        self.xpath = xpath
        self.children = children

        self.content = content
        self.content_len = len(content)

    def __init__(self, id: str, source_url: str, xpath: str, content: str):
        self.id = id
        self.source_url = source_url
        self.xpath = xpath
        self.children = None

        self.content = content
        self.content_len = len(content)

    def __str__(self):
        if len(self.children) == 0:
            return self.content
        
        resp = ""
        for child in self.children:
            resp += str(child)

        return resp

    @staticmethod
    def build_complex_id(chunks):
        complex_id = "U"

        for chunk in chunks:
            complex_id += '_' + chunk.id

        return complex_id

    @classmethod
    def unite_chunks(cls, chunks):
        complex_id = cls.build_complex_id(chunks)
        source_url = chunks[0].source_url
        children = chunks
    
        chunk = Chunk(id=complex_id, source_url=source_url, children=children)
        return chunk
    