from langchain_core.tools import StructuredTool
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.ticket_service import TicketService
from app.schemas.ticket import TicketUpdateRequest

def get_escalate_tool(session: AsyncSession, user_id: str):
    async def wrapper(ticket_id: str, reason: str) -> str:
        service = TicketService(session)
        try:
            # Escalation = mark ticket as high priority + add a comment with escalation note
            updated = await service.update_ticket(
                ticket_id=ticket_id,
                user_id=user_id,
                request=TicketUpdateRequest(
                    priority="high",
                    comment=f"ESCALATED TO HUMAN: {reason}"
                )
            )
            return f"Ticket {ticket_id} escalated. A human agent will review it."
        except Exception as e:
            return f"Escalation failed: {e}"
    return StructuredTool.from_function(
        name="escalate_to_human",
        description="Escalate a ticket to a human support agent. Input: ticket_id, reason.",
        func=wrapper,
        coroutine=wrapper,
    )