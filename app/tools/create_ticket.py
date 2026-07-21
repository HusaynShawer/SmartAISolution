from langchain_core.tools import StructuredTool
from sqlalchemy.ext.asyncio import AsyncSession
from services.ticket_service import TicketService
from schemas.ticket import TicketCreateRequest

def get_create_ticket_tool(session: AsyncSession, user_id: str):
    async def wrapper(subject: str, description: str, priority: str = "medium") -> str:
        service = TicketService(session)
        try:
            ticket = await service.create_ticket(
                user_id=user_id,
                request=TicketCreateRequest(subject=subject, description=description, priority=priority)
            )
            return f"Ticket created with ID {ticket.id}, status: {ticket.status}"
        except Exception as e:
            return f"Failed to create ticket: {e}"
    return StructuredTool.from_function(
        name="create_support_ticket",
        description="Create a new support ticket. Input: subject, description, priority (low/medium/high).",
        func=wrapper,
        coroutine=wrapper,
    )