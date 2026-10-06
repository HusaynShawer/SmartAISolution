from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.embedding import Embedding


class EmbeddingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def bulk_insert(self, embeddings_data: list[dict]) -> None:
        embeddings = [Embedding(**data) for data in embeddings_data]
        self.session.add_all(embeddings)
        await self.session.commit()

    async def similarity_search(
        self, query_embed: list[float], top_k: int = 5
    ) -> list[Embedding]:
        query = (
            select(Embedding)
            .order_by(Embedding.embedding.cosine_distance(query_embed))
            .limit(top_k)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
