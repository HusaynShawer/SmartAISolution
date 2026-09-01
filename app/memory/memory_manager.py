from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.conversation_repo import MessageRepository


class MemoryManager:
    """Handles persisting and loading conversation messages."""

    def __init__(self, session: AsyncSession) -> None:
        self.msg_repo = MessageRepository(session)

    async def get_recent_history(
        self, conversation_id: str, limit: int = 20
    ) -> list[dict]:
        messages = await self.msg_repo.get_message_history(
            conversation_id, limit=limit
        )
        return [{"role": m.role, "content": m.content} for m in messages]

    async def add_user_message(self, conversation_id: str, content: str) -> dict:
        message = await self.msg_repo.add_message(
            conversation_id, "user", content
        )
        return {"role": message.role, "content": message.content}

    async def add_assistant_message(
        self, conversation_id: str, content: str
    ) -> dict:
        message = await self.msg_repo.add_message(
            conversation_id, "assistant", content
        )
        return {"role": message.role, "content": message.content}
