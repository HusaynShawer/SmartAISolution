import logging

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.document import Document

logger = logging.getLogger(__name__)


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self, user_id: str, file_name: str, content_type: str, size_bytes: int
    ) -> Document:
        doc = Document(
            user_id=user_id,
            filename=file_name,
            content_type=content_type,
            size_bytes=size_bytes,
        )
        self.session.add(doc)
        await self.session.commit()
        await self.session.refresh(doc)
        logger.info("Created document %s for user %s", doc.id, user_id)
        return doc

    async def get_by_id(self, doc_id: str) -> Document | None:
        query = select(Document).where(Document.id == doc_id)
        result = await self.session.execute(query)
        doc = result.scalar_one_or_none()
        logger.debug(
            "Fetched document by id: %s -> %s", doc_id, getattr(doc, "id", None)
        )
        return doc

    async def delete(self, doc_id: str) -> None:
        stmt = sa_delete(Document).where(Document.id == doc_id)
        await self.session.execute(stmt)
        await self.session.commit()
        logger.info("Deleted document %s", doc_id)