import os
import tempfile
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.repositories.document_repo import DocumentRepository
from repositories.embedding_repo import EmbeddingRepository
from rag.laoder import extract_text_from_pdf, extract_text_from_markdown, extract_text_from_txt
from app.rag.splitter import split_text
from app.rag.embedder import generate_embeddings
import logging

logger = logging.Logger(__name__)

ALLOWED_EXTENSIONS = {"pdf", "md", "txt"}

class Document_service:
    def __init__(self,session:AsyncSession):
        self.doc_repo = DocumentRepository
        self.session = session
        self.emb_repo = EmbeddingRepository
    
    async def upload_and_process(self,file:UploadFile,user_id:str)->dict:
        ext = file.filename.split(".")[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            logger.info("user try to upload non allwoed file")
            raise HTTPException(
                status_code=400,detail="UnSpported file"
            )
        with tempfile.TemporaryFile(delete=False,suffix=f".{ext}") as temp_file:
            content = await file.read()
            if len(content)>settings.MAX_FILE_SIZE * 1024* 1024:
                raise HTTPException(status_code=400,detail="File size is very laarge")
                os.unlink(temp_file)
            temp_file.write(content)
            tmp_path = temp_file.name
        logger.info(f"the emp file path {tmp_path}")
        if ext == "pdf":
            text=extract_text_from_pdf(tmp_path)
        elif ext == "md":
            text = extract_text_from_markdown(tmp_path)
        elif ext == "txt":
            text = extract_text_from_txt(tmp_path)

        os.unlink(tmp_path)
        
        if not text.strip():
            logger.info("text arent found")
            raise HTTPException(status_code=400,detail="no extractable text found")
        
        doc = self.doc_repo.create(
            user_id=user_id,
            file_name=file.filename,
            content_type=file.content_type or f"text/{ext}",
            size_bytes=len(content)
        )
        chunks = split_text(doc)
        embeddings = await generate_embeddings(chunks)

        embeddings_data = []

        for idx,(chunk,embed) in enumerate(zip(chunks,embeddings)):
            embeddings_data.append({
                "document_id": doc.id,
                "chunk_index": idx,
                "content": chunk,
                "embedding": embed,
                "metadata_": None,  
            })

        await self.emb_repo.bulk_insert(embeddings_data)

        return {"documnet_id":doc.id, "chunks":len(chunks)}