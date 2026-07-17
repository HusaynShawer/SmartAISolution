from langchain_text_splitters import RecursiveCharacterTextSplitter
from core.config import settings

text_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", " ", ""],  # تعديل إلى a
    chunk_size=400,
    chunk_overlap=50
)
def split_text(text:str)->list[str]:
    return text_splitter.split_text(text)