from langchain_core.tools import StructuredTool
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.ticket import TicketUpdateRequest
from services.ticket_service import TicketService


def get_escalate_tool(session: AsyncSession, user_id: str) -> StructuredTool:
    async def wrapper(ticket_id: str, reason: str) -> str:
        service = TicketService(session)
        try:
            await service.update_ticket(
                ticket_id=ticket_id,
                user_id=user_id,
                request=TicketUpdateRequest(
                    priority="high",
                    comment=f"ESCALATED TO HUMAN: {reason}",
                ),
            )
            return (
                f"Ticket {ticket_id} escalated. A human agent will review it."
            )
        except Exception as exc:
            return f"Escalation failed: {exc}"

    return StructuredTool.from_function(
        name="escalate_to_human",
        description=(
            "Escalate a ticket to a human support agent. Input: ticket_id, reason."
        ),
        func=wrapper,
        coroutine=wrapper,
    )
