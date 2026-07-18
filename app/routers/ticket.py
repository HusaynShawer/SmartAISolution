from fastapi import HTTPException, Query, status,APIRouter,Depends,Query
from sqlalchemy.ext.asyncio import AsyncSession
from services.ticket_service import TicketService
from database.session import get_db
from core.dependencies import get_current_user
from models.user import User
from schemas.ticket import (
    TicketCreateRequest, TicketUpdateRequest, TicketResponse, TicketListResponse,
)

router = APIRouter(prefix="/tickets",tags=["Tickets"])

@router.post("",response_model=TicketResponse,status_code=201)
async def createTicket(
        request:TicketCreateRequest,
        db:AsyncSession=Depends(get_db),
        current_user:User = Depends(get_current_user)
):
    service = TicketService(db)
    return await service.create_ticket(current_user.id, request)

@router.get("", response_model=TicketListResponse)
async def list_tickets(skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, pattern="^(open|in_progress|resolved|closed)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TicketService(db)
    return await service.get_ticket_list(current_user.id, skip, limit, status)

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
