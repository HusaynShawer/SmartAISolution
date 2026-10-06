from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.config import settings

text_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", " ", ""],
    chunk_size=settings.CHUNK_SIZE,
    chunk_overlap=settings.CHUNK_OVERLAP,
)


def split_text(text: str) -> list[str]:
    """Split text into overlapping chunks for embedding."""
    return text_splitter.split_text(text)
