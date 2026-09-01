# ticket_repo.py
import logging

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.ticket import Ticket
from models.ticket_update import TicketUpdate

logger = logging.getLogger(__name__)

class TicketRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: str, subject: str,
                     description: str, priority: str = "medium") -> Ticket:
        logger.info("Creating ticket for user %s with priority %s", user_id, priority)
        ticket = Ticket(
            user_id=user_id,
            subject=subject,
            description=description,
            priority=priority,
        )
        self.session.add(ticket)
        await self.session.commit()
        await self.session.refresh(ticket)
        logger.info("Ticket %s created successfully", ticket.id)
        return ticket

    async def get_ticket_by_id(self, ticket_id: str) -> Ticket | None:
        logger.debug("Fetching ticket %s", ticket_id)
        query = select(Ticket).where(Ticket.id == ticket_id)
        result = await self.session.execute(query)
        ticket = result.scalar_one_or_none()
        if not ticket:
            logger.warning("Ticket %s not found", ticket_id)
        return ticket

    async def get_ticket_list_by_id(
            self, user_id: str, limit: int = 10, skip: int = 0,
            status: str | None = None
    ) -> tuple[list[Ticket], int]:
        logger.info("Fetching tickets for user %s | skip=%s limit=%s status=%s", user_id, skip, limit, status)
        cond = [Ticket.user_id == user_id]
        if status:
            cond.append(Ticket.status == status)

        query_count = select(func.count()).select_from(Ticket).where(*cond)
        total_result = await self.session.execute(query_count)
        total = total_result.scalar() or 0

        query = (
            select(Ticket).where(*cond)  
            .order_by(desc(Ticket.updated_at))
            .offset(skip).limit(limit)
        )
        result = await self.session.execute(query)
        tickets = list(result.scalars().all())
        logger.info("Found %s tickets (total=%s) for user %s", len(tickets), total, user_id)
        return tickets, total

    async def update(self, ticket: Ticket, **kwargs) -> Ticket:
        logger.info("Updating ticket %s with fields: %s", ticket.id, list(kwargs.keys()))
        for key, value in kwargs.items():
            if hasattr(ticket, key) and value is not None:
                setattr(ticket, key, value)
        await self.session.commit()
        await self.session.refresh(ticket)
        logger.info("Ticket %s updated successfully", ticket.id)
        return ticket

    async def add_update(self, ticket_id: str, content: str, created_by: str) -> TicketUpdate:
        logger.info("Adding update to ticket %s by user %s", ticket_id, created_by)
        update = TicketUpdate(
            ticket_id=ticket_id,
            content=content,
            created_by=created_by,
        )
        self.session.add(update)
        await self.session.commit()
        await self.session.refresh(update)
        logger.debug("Update added to ticket %s", ticket_id)
        return update

    async def get_updates(self, ticket_id: str) -> list[TicketUpdate]:
        logger.debug("Fetching updates for ticket %s", ticket_id)
        stmt = (
            select(TicketUpdate)
            .where(TicketUpdate.ticket_id == ticket_id)
            .order_by(TicketUpdate.created_at.asc())
        )
        result = await self.session.execute(stmt)
        updates = list(result.scalars().all())
        logger.debug("Found %s updates for ticket %s", len(updates), ticket_id)
        return updates

    async def search_similar(self, query_text: str, limit: int = 5) -> list[Ticket]:
        logger.info("Searching tickets with query: '%s'", query_text)
        stmt = (
            select(Ticket)
            .where(
                Ticket.subject.ilike(f"%{query_text}%") |
                Ticket.description.ilike(f"%{query_text}%")
            )
            .order_by(desc(Ticket.updated_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        tickets = list(result.scalars().all())
        logger.info("Search returned %s results for query: '%s'", len(tickets), query_text)
        return tickets