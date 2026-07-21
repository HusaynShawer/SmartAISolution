import logging
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.ticket_repo import TicketRepository
from schemas.ticket import (
    TicketCreateRequest, TicketUpdateRequest, TicketResponse,
    TicketUpdateResponse, TicketListResponse,
)

logger = logging.getLogger(__name__)


class TicketService:
    def __init__(self, session: AsyncSession):
        self.ticket_repo = TicketRepository(session)

    async def create_ticket(self, user_id: str, request: TicketCreateRequest) -> TicketResponse:
        logger.info("User %s creating ticket with subject: %s", user_id, request.subject)
        ticket = await self.ticket_repo.create(
            user_id=user_id,
            subject=request.subject,
            description=request.description,
            priority=request.priority,
        )
        logger.info("Ticket %s created successfully for user %s", ticket.id, user_id)

        self.ticket_repo.add_update(
            ticket_id=ticket.id,
            content=f"Ticket created with priority {ticket.priority}",
            created_by=user_id,
        )
        return await self._to_response(ticket)

    async def get_ticket(self, ticket_id: str, user_id) -> TicketListResponse:
        logger.info("User %s fetching ticket %s", user_id, ticket_id)
        ticket = await self.ticket_repo.get_ticket_by_id(ticket_id)
        if not ticket or ticket.user_id != user_id:
            logger.warning("Ticket %s not found or unauthorized access by user %s", ticket_id, user_id)
            raise HTTPException(status_code=400, detail="Ticket not found")

        return await self._to_response(ticket)

    async def get_ticket_list(self, user_id, skip: int = 0, limit: int = 10,
                               status: str | None = None) -> list[TicketListResponse]:
        logger.info("User %s fetching ticket list | skip=%s limit=%s status=%s", user_id, skip, limit, status)
        tickets, total = await self.ticket_repo.get_ticket_list_by_id(
            user_id=user_id,
            skip=skip,
            limit=limit,
            status=status,
        )
        logger.info("Found %s tickets for user %s", total, user_id)

        ticket_response = [await self._to_response(t) for t in tickets]
        return TicketListResponse(tickets=ticket_response, total=total, skip=skip, limit=limit)

    async def update_ticket(self, user_id: str, ticket_id: str, request: TicketUpdateRequest) -> TicketResponse:
        logger.info("User %s updating ticket %s", user_id, ticket_id)
        ticket = await self.ticket_repo.get_ticket_by_id(ticket_id=ticket_id)
        if not ticket or ticket.user_id != user_id:
            logger.warning("Ticket %s not found or unauthorized update attempt by user %s", ticket_id, user_id)
            raise HTTPException(status_code=400, detail="Ticket not found")

        updates = {}
        if request.status:
            updates["status"] = request.status
        if request.priority:
            updates["priority"] = request.priority

        if updates:
            logger.info("Applying updates to ticket %s: %s", ticket_id, updates)
            ticket = await self.ticket_repo.update(ticket=ticket, **updates)

        if request.comment:
            logger.info("Adding comment to ticket %s by user %s", ticket_id, user_id)
            await self.ticket_repo.add_update(
                ticket_id=ticket_id,
                content=request.comment,
                created_by=user_id,
            )

        logger.info("Ticket %s updated successfully", ticket_id)
        return await self._to_response(ticket)

    async def _to_response(self, ticket) -> TicketResponse:
        logger.debug("Building response for ticket %s", ticket.id)
        updates = await self.ticket_repo.get_updates(ticket.id)
        return TicketResponse(
            id=ticket.id,
            user_id=ticket.user_id,
            subject=ticket.subject,
            description=ticket.description,
            status=ticket.status,
            priority=ticket.priority,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            updates=[TicketUpdateResponse.model_validate(u) for u in updates],
        )