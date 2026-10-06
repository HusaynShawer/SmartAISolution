from langchain_core.tools import StructuredTool
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.ticket_repo import TicketRepository


async def search_ticket_func(
    query: str, user_id: str, session: AsyncSession
) -> list[dict]:
    ticket_repo = TicketRepository(session=session)
    tickets = await ticket_repo.search_similar(query_text=query)
    return [
        {
            "id": ticket.id,
            "subject": ticket.subject,
            "status": ticket.status,
            "priority": ticket.priority,
        }
        for ticket in tickets
        if ticket.user_id == user_id
    ]


def get_search_ticket_tool(
    session: AsyncSession, user_id: str
) -> StructuredTool:
    async def wrapper(query: str) -> str:
        results = await search_ticket_func(
            query=query, user_id=user_id, session=session
        )
        if not results:
            return "No matching tickets found."
        return "\n".join(
            [f"{t['subject']} (status: {t['status']})" for t in results]
        )

    return StructuredTool.from_function(
        name="search_previous_tickets",
        description=(
            "Search previous support tickets for similar issues. "
            "Input: search query string."
        ),
        func=wrapper,
        coroutine=wrapper,
    )