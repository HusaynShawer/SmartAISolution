from langchain_text_splitters import RecursiveCharacterTextSplitter
from core.config import settings

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = settings.CHUNK_SIZE,
    chunk_overlap=settings.CHUNK_OVERLAB,
    seperators = ['\n\n','\n'," ",""]
)
def split_text(text:str)->list[str]:
    return text_splitter.split_text(text)