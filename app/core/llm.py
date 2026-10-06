
from langchain_openai import ChatOpenAI

from core.config import settings


def get_llm(temperature: float = 0.1, streaming: bool = True) -> ChatOpenAI:
    """Create an LLM instance using OpenRouter (OpenAI-compatible API)."""
    return ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        temperature=temperature,
        streaming=streaming,
        timeout=settings.REQUEST_TIMEOUT_SECONDS,
        max_retries=3,
        default_headers={
            "HTTP-Referer": settings.OPENROUTER_HTTP_REFERER,
            "X-Title": settings.OPENROUTER_APP_NAME,
        },
    )


def get_embedding_model():
    """Get the embedding model client.

    Note: OpenRouter doesn't support embeddings, so we use OpenAI directly.
    """
    from openai import AsyncOpenAI

    return AsyncOpenAI(
        api_key=settings.EMBEDDING_API_KEY,
        base_url=settings.EMBEDDING_BASE_URL,
        timeout=settings.REQUEST_TIMEOUT_SECONDS,
        max_retries=3,
    )
