from langchain_core.tools import StructuredTool
from sqlalchemy.ext.asyncio import AsyncSession

from rag.retriever import retrieve_relevant_chunks


async def search_docs_func(query: str, session: AsyncSession) -> list[dict]:
    return await retrieve_relevant_chunks(query=query, session=session)


def get_search_docs_tool(session: AsyncSession) -> StructuredTool:
    async def wrapper(query: str) -> str:
        result = await search_docs_func(query, session)
        if not result:
            return "No relevant documentation found"
        return "\n\n".join([r["content"] for r in result])

    return StructuredTool.from_function(
        name="search_documentation",
        description="Search internal documentation. Input: search query string.",
        func=wrapper,
        coroutine=wrapper,
    )
