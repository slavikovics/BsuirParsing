from chunk_base import Chunk
from image_chunk import ImageChunk
from text_chunk import TextChunk

class ChunkAggregator:

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks

    def all_child_images(self):
        found_images = []

        for child in self.chunks:
            if child is ImageChunk:
                found_images.append(child)

        return found_images
    
    def all_child_texts(self):
        found_texts = []

        for child in self.chunks:
            if child is TextChunk:
                found_texts.append(child.content)

        return found_texts
