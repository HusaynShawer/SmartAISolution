from langchain_core.tools import StructuredTool
from repositories.ticket_repo import TicketRepository
from sqlalchemy.ext.asyncio import AsyncSession

async def search_ticket_func(query:str, user_id,session:AsyncSession)->list[dict]:
    ticket_repo = TicketRepository(session=session)
    ticket = ticket_repo.search_similar(query_text=query)
    return [
        {
            "id":t.id,"subject":t.subject,"priority":t.priority
        } for t in ticket if t.user_id == user_id
    ]

def get_search_ticket_tool(session:AsyncSession):
    async def wrapper(query:str,user_id:str,session)->str:
        
        results = await search_ticket_func(query=query,user_id=user_id,session=session)
        if not results:
            return "No matching tickets found."
        return "\n".join([f"{t['subject']} (status: {t['status']})" for t in results])
    
    return StructuredTool.from_function(
        name="search_previous_tickets",
        description="Search previous support tickets for similar issues. Input: query string.",
        func=wrapper,
        coroutine=wrapper,
    )