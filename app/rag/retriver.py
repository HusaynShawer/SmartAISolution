from sqlalchemy.ext.asyncio import AsyncSession
from repositories.embedding_repo import EmbeddingRepository
from rag.embedder import generate_embeddings

async def retrieve_relevent_chunks(
        query:str,
        session:AsyncSession,top_k:int=5
)->list[dict]:
    
    emb_repo = EmbeddingRepository(session)
    query_embed = (await generate_embeddings([query]))[0]
    result = emb_repo.similarity_search(query_embed=query_embed,top_k=top_k)

    return [
            {"content":r.content,"metadata":r.metadat_,"score":None}
            for r in result
            ]