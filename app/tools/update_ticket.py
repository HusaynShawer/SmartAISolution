from langchain_core.tools import StructuredTool
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.ticket_service import TicketService
from app.schemas.ticket import TicketUpdateRequest

def get_update_ticket_tool(session: AsyncSession, user_id: str):
    async def wrapper(ticket_id: str, status: str = None, comment: str = None) -> str:
        service = TicketService(session)
        try:
            updated = await service.update_ticket(
                ticket_id=ticket_id,
                user_id=user_id,
                request=TicketUpdateRequest(status=status, comment=comment)
            )
            return f"Ticket {ticket_id} updated. New status: {updated.status}"
        except Exception as e:
            return f"Failed to update ticket: {e}"
    return StructuredTool.from_function(
        name="update_support_ticket",
        description="Update an existing ticket's status or add a comment. Input: ticket_id, optional status, optional comment.",
        func=wrapper,
        coroutine=wrapper,
    )