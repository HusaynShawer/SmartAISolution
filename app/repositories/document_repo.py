from models.document import Document
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)
class DocumentRepository:
    def __init__(self,session:AsyncSession):
        self.session = session
    
    async def create(self,user_id:str,file_name:str, content_type:str,size_bytes:int)->Document:
        doc = Document(
            user_id=user_id,
            filename=file_name,
            content_type=content_type,
            size_bytes=size_bytes
        )
        self.session.add(doc)
        await self.session.commit()
        await self.session.refresh(doc)
        logger.info("Created document %s for user %s", doc.id, user_id)
        return doc
    async def get_by_id(self,doc_id:str)->Document:
        query = select(Document).where(Document.id==doc_id)
        result = self.session.execute(query)
        doc = await result.scalar_one_or_none()
        logger.debug("Fetched document by id: %s -> %s", doc_id, getattr(doc, 'id', None))
        return doc
    