from chunk_base import Chunk

class ImageChunk(Chunk):

    def __init__(self, id: str, source_url: str, xpath: str, image_label: str, image_url: str):
        super().__init__(id=id, source_url=source_url, xpath=xpath, content=image_label)
        self.image_url = image_url

    def __str__(self):
        return None