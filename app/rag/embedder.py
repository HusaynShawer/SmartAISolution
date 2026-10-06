import logging

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from core.config import settings

logger = logging.getLogger(__name__)


def _create_client():
    try:
        import cohere

        return cohere.AsyncClient(api_key=settings.EMBEDDING_API_KEY)
    except Exception as exc:  # pragma: no cover - import-time failure
        logger.warning("Failed to init Cohere client: %s", exc)
        return None


co = _create_client()


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def generate_embeddings(
    texts: list[str], model: str | None = None
) -> list[list[float]]:
    if co is None:
        raise RuntimeError("Cohere client is not available")
    model = model or settings.EMBEDDING_MODEL
    response = await co.embed(
        texts=texts,
        model=model,
        input_type="search_document",
    )
    return [list(embedding) for embedding in response.embeddings]