import logging

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.conversation_repo import ConversationRepository, MessageRepository
from schemas.conversation import (
    ConversationDetailResponse,
    ConversationResponse,
    MessageResponse,
)

logger = logging.getLogger(__name__)


class ConversationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.conv_repo = ConversationRepository(session)
        self.msg_repo = MessageRepository(session)

    async def create_conversation(
        self, user_id: str, title: str | None = None
    ) -> ConversationResponse:
        logger.info("Creating conversation for user: %s", user_id)
        conv = await self.conv_repo.create(user_id=user_id, title=title)
        logger.info("Conversation created with id: %s", getattr(conv, "id", None))
        return ConversationResponse.model_validate(conv)

    async def get_user_conversations(
        self, user_id: str, skip: int, limit: int
    ) -> list[ConversationResponse]:
        logger.info(
            "Listing conversations for user: %s (skip=%s, limit=%s)",
            user_id, skip, limit,
        )
        convs = await self.conv_repo.list_conv_by_user(
            user_id=user_id, skip=skip, limit=limit
        )
        return [ConversationResponse.model_validate(c) for c in convs]

    async def get_conversation_detail(
        self, user_id: str, conv_id: str, limit: int
    ) -> ConversationDetailResponse | None:
        logger.info(
            "Fetching conversation detail for conv_id=%s user=%s", conv_id, user_id
        )
        conv = await self.conv_repo.get_conv_by_id(conv_id=conv_id)
        if not conv or conv.user_id != user_id:
            logger.warning(
                "Conversation not found or access denied conv_id=%s user=%s",
                conv_id, user_id,
            )
            return None

        messages = await self.msg_repo.get_message_history(
            conversation_id=conv_id, limit=limit
        )

        return ConversationDetailResponse(
            **ConversationResponse.model_validate(conv).model_dump(),
            messages=[MessageResponse.model_validate(msg) for msg in messages],
        )

    async def delete_conversation(self, user_id: str, conv_id: str) -> bool:
        logger.info("Deleting conversation conv_id=%s user=%s", conv_id, user_id)
        conv = await self.conv_repo.get_conv_by_id(conv_id=conv_id)
        if not conv or conv.user_id != user_id:
            logger.warning(
                "Delete failed: conversation not found or access denied "
                "conv_id=%s user=%s",
                conv_id, user_id,
            )
            return False

        await self.conv_repo.delete_conv(conv_id=conv_id)
        logger.info("Conversation deleted conv_id=%s", conv_id)
        return True
