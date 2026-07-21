from langchain_core.tools import StructuredTool
from sqlalchemy.ext.asyncio import AsyncSession
from rag.retriver import retrieve_relevent_chunks


async def search_docs_func(query:str,session:AsyncSession):
    chunks = await retrieve_relevent_chunks(query=query,session=session)
    return chunks
def get_search_docs_tool(session:AsyncSession):
    async def wrapper(query:str)->str:
        result = await search_docs_func(query,session)
        if not result:
            return "No relevent documentation found"
        return "/n/n".join([r["content"] for r in result])
    return StructuredTool.from_function(
        name="search_documentation",
        description="Search internal documentation. Input: search query string.",
        func=wrapper,
        coroutine=wrapper,
    )
    