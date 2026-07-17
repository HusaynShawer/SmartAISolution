from sqlalchemy.ext.asyncio import AsyncSession
from models.embedding import Embedding
from sqlalchemy import select

class EmbeddingRepository:
    def __init__(self,session:AsyncSession):
        self.session = session
    async def bulk_insert(self,embed_data:dict)-> None:

        for data in embed_data:
            emb = Embedding(**data)
            self.session.add(emb)
        await self.session.commit()
        await self.session.refresh(emb)
 
    async def similarity_search(self,query_embed:list[float],top_k:int=5)-> list[Embedding]:
        query = (
            select(Embedding)
            .order_by(Embedding.embedding.cosine_distance(query_embed))
            .limit(top_k)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())