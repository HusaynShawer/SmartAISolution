from core.config import settings
import cohere

co = cohere.AsyncClient(api_key=settings.COHERE_API_KEY)

async def generate_embeddings(texts: list[str], model: str = None) -> list[list[float]]:
    model = model or settings.EMBEDDING_MODEL
    response = await co.embed(
        texts=texts,
        model=model,
        input_type="search_document"
    )
    return response.embeddings