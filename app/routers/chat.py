import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db
from core.dependencies import get_current_user
from models.user import User
from services.agent_service import AgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    response: str


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AgentService(db)
    result = await service.process_message(
        user_id=current_user.id,
        conversation_id=request.conversation_id,
        message=request.message,
    )
    return result


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AgentService(db)

    async def event_generator():
        try:
            async for token in service.process_message_stream(
                user_id=current_user.id,
                conversation_id=request.conversation_id,
                message=request.message,
            ):
                if token.startswith("__conversation_id__:"):
                    conv_id = token.split(":", 1)[1]
                    yield f"data: {json.dumps({'conversation_id': conv_id})}\n\n"
                else:
                    yield f"data: {json.dumps({'token': token})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.exception("Streaming error")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable buffering in nginx
        },
    )