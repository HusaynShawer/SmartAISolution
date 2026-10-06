from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user
from database.session import get_db
from models.user import User
from schemas.ticket import (
    TicketCreateRequest,
    TicketListResponse,
    TicketResponse,
    TicketUpdateRequest,
)
from services.ticket_service import TicketService

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    request: TicketCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TicketService(db)
    return await service.create_ticket(current_user.id, request)


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(
        None, alias="status", pattern="^(open|in_progress|resolved|closed)$"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TicketService(db)
    return await service.get_ticket_list(
        current_user.id, skip, limit, status_filter
    )


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TicketService(db)
    return await service.get_ticket(ticket_id, current_user.id)


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: str,
    request: TicketUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TicketService(db)
    return await service.update_ticket(ticket_id, current_user.id, request)
