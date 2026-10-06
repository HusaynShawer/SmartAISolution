import os
import tempfile

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from rag.embedder import generate_embeddings
from rag.loader import (
    extract_text_from_markdown,
    extract_text_from_pdf,
    extract_text_from_txt,
)
from rag.splitter import split_text
from repositories.document_repo import DocumentRepository
from repositories.embedding_repo import EmbeddingRepository

ALLOWED_EXTENSIONS = {"pdf", "md", "txt"}


class DocumentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.emb_repo = EmbeddingRepository(session)

    async def upload_and_process(self, file: UploadFile, user_id: str) -> dict:
        filename = file.filename or ""
        ext = filename.split(".")[-1].lower() if "." in filename else ""

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {ext or 'unknown'}",
            )

        content = await file.read()
        max_bytes = settings.MAX_FILE_SIZE * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size is too large",
            )

        tmp_path = self._write_temp_file(content, ext)

        try:
            text = await self._extract_text(ext, tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        if not text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="no extractable text found",
            )

        doc = await self.doc_repo.create(
            user_id=user_id,
            file_name=filename,
            content_type=file.content_type or f"text/{ext}",
            size_bytes=len(content),
        )

        chunks = split_text(text)
        if not chunks:
            await self.doc_repo.delete(doc.id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text could not be split into chunks",
            )

        try:
            embeddings = await generate_embeddings(chunks)
        except Exception as exc:
            await self.doc_repo.delete(doc.id)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Embedding generation failed: {exc}",
            ) from exc

        if len(chunks) != len(embeddings):
            await self.doc_repo.delete(doc.id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"Failed to process document: Vector generation mismatch "
                    f"({len(embeddings)} vectors for {len(chunks)} chunks)."
                ),
            )

        embeddings_data = [
            {
                "document_id": doc.id,
                "chunk_index": idx,
                "content": chunk,
                "embedding": embed,
                "metadata_": None,
            }
            for idx, (chunk, embed) in enumerate(
                zip(chunks, embeddings, strict=True)
            )
        ]

        await self.emb_repo.bulk_insert(embeddings_data)

        return {
            "document_id": doc.id,
            "filename": filename,
            "chunks": len(chunks),
            "status": "processed",
        }

    def _write_temp_file(self, content: bytes, ext: str) -> str:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=f".{ext}"
        ) as temp_file:
            temp_file.write(content)
            return temp_file.name

    async def _extract_text(self, ext: str, tmp_path: str) -> str:
        if ext == "pdf":
            return await extract_text_from_pdf(tmp_path)
        if ext == "md":
            return await extract_text_from_markdown(tmp_path)
        return await extract_text_from_txt(tmp_path)