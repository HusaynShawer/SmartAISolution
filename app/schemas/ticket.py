from datetime import datetime

from pydantic import BaseModel, Field


class TicketCreateRequest(BaseModel):
    subject: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")

class TicketUpdateRequest(BaseModel):
    status: str | None = Field(None, pattern="^(open|in_progress|resolved|closed)$")
    priority: str | None = Field(None, pattern="^(low|medium|high)$")
    comment: str | None = None  # adds a ticket_update entry

class TicketUpdateResponse(BaseModel):
    id: str
    ticket_id: str
    content: str
    created_by: str
    created_at: datetime

    model_config = {"from_attributes": True}

class TicketResponse(BaseModel):
    id: str
    user_id: str
    subject: str
    description: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime
    updates: list[TicketUpdateResponse] = []

    model_config = {"from_attributes": True}

class TicketListResponse(BaseModel):
    tickets: list[TicketResponse]
    total: int
    skip: int
    limit: int