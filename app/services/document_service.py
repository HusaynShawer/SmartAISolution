import os
import tempfile
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import settings
from repositories.document_repo import DocumentRepository
from repositories.embedding_repo import EmbeddingRepository
from rag.laoder import extract_text_from_pdf, extract_text_from_markdown, extract_text_from_txt
from rag.splitter import split_text
from rag.embedder import generate_embeddings
import logging

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"pdf", "md", "txt"}

class DocumentService:
    def __init__(self, session: AsyncSession):
        self.doc_repo = DocumentRepository(session)
        self.session = session
        self.emb_repo = EmbeddingRepository(session)

    async def upload_and_process(self, file: UploadFile, user_id: str) -> dict:
        ext = file.filename.split(".")[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            logger.info("User attempted to upload unsupported file type: %s", ext)
            raise HTTPException(
                status_code=400, detail="Unsupported file"
            )
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as temp_file:
            content = await file.read()
            # ensure temporary file is removed before raising an exception
            if len(content) > settings.MAX_FILE_SIZE * 1024 * 1024:
                tmp_path_to_delete = temp_file.name
                temp_file.close()
                os.unlink(tmp_path_to_delete)
                raise HTTPException(status_code=400, detail="File size is very large")
                
            temp_file.write(content)
            tmp_path = temp_file.name
            
        logger.info(f"Temporary file created at: {tmp_path}")
        
        try:
            logger.info("Starting text extraction for file: %s", file.filename)
            if ext == "pdf":
                text = await extract_text_from_pdf(tmp_path)
            elif ext == "md":
                text = await extract_text_from_markdown(tmp_path)
            elif ext == "txt":
                text = await extract_text_from_txt(tmp_path)
            logger.info("Text extraction completed for file: %s", file.filename)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
        if not text.strip():
            logger.info("No extractable text found in file: %s", file.filename)
            raise HTTPException(status_code=400, detail="no extractable text found")
        
        doc = await self.doc_repo.create(
            user_id=user_id,
            file_name=file.filename,
            content_type=file.content_type or f"text/{ext}",
            size_bytes=len(content)
        )
        
        chunks = await split_text(text) 
        embeddings = await generate_embeddings(chunks)

        if len(chunks) != len(embeddings):
            logger.error("Mismatch: %d chunks but %d embeddings", len(chunks), len(embeddings))
            await self.doc_repo.delete(doc.id)
            await self.session.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process document: Vector generation mismatch ({len(embeddings)} vectors for {len(chunks)} chunks)."
            )

        embeddings_data = []
        for idx, (chunk, embed) in enumerate(zip(chunks, embeddings)):
            embeddings_data.append({
                "document_id": doc.id,
                "chunk_index": idx,
                "content": chunk,
                "embedding": embed,
                "metadata_": None,  
            })

        await self.emb_repo.bulk_insert(embeddings_data)
        await self.session.commit()
        logger.info("Document and embeddings stored successfully for document id: %s", doc.id)