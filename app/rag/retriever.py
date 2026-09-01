from sqlalchemy.ext.asyncio import AsyncSession

from rag.embedder import generate_embeddings
from repositories.embedding_repo import EmbeddingRepository


async def retrieve_relevant_chunks(
    query: str,
    session: AsyncSession,
    top_k: int = 5,
) -> list[dict]:
    """Retrieve the most semantically relevant document chunks for a query."""
    embedding_repo = EmbeddingRepository(session)
    query_embedding = (await generate_embeddings([query]))[0]
    results = await embedding_repo.similarity_search(
        query_embed=query_embedding,
        top_k=top_k,
    )

    return [
        {
            "content": result.content,
            "metadata": result.metadata_,
            "score": None,
        }
        for result in results
    ]
