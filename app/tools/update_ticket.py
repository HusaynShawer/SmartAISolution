from langchain_core.tools import StructuredTool
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.ticket import TicketUpdateRequest
from services.ticket_service import TicketService


def get_update_ticket_tool(session: AsyncSession, user_id: str) -> StructuredTool:
    async def wrapper(
        ticket_id: str,
        status: str | None = None,
        comment: str | None = None,
    ) -> str:
        service = TicketService(session)
        try:
            updated = await service.update_ticket(
                ticket_id=ticket_id,
                user_id=user_id,
                request=TicketUpdateRequest(status=status, comment=comment),
            )
            return f"Ticket {ticket_id} updated. New status: {updated.status}"
        except Exception as exc:
            return f"Failed to update ticket: {exc}"

    return StructuredTool.from_function(
        name="update_support_ticket",
        description=(
            "Update an existing ticket's status or add a comment. "
            "Input: ticket_id, optional status, optional comment."
        ),
        func=wrapper,
        coroutine=wrapper,
    )