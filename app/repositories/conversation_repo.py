from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import logging

from models.conversation import Conversation
from models.message import Message

logger = logging.getLogger(__name__)


class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session  

    async def create(self, user_id: str, title: str | None = None) -> Conversation:
        conv = Conversation(user_id=user_id, title=title or "New conversation")
        self.session.add(conv)
        await self.session.commit()
        await self.session.refresh(conv)
        return conv  

    async def get_conv_by_id(self, conv_id: str) -> Conversation | None:
        query = select(Conversation).where(Conversation.id == conv_id)  
        result = await self.session.execute(query)  
        return result.scalar_one_or_none()

    async def list_conv_by_user(self, user_id: str, skip: int = 0, limit: int = 20) -> list[Conversation]:
        query = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.updated_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)  
        return list(result.scalars().all())

    async def update_title(self, conv_id: str, title: str) -> None:
        conv = await self.get_conv_by_id(conv_id=conv_id)  
        if not conv:
            logger.info("Conversation not found for id: %s", conv_id)
            return  
        conv.title = title
        await self.session.commit()  

    async def delete_conv(self, conv_id: str) -> None:
        conv = await self.get_conv_by_id(conv_id=conv_id)  
        if not conv:
            logger.info("Conversation not found for id: %s", conv_id)
            return  
        await self.session.delete(conv)
        await self.session.commit()


class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_message(self, conversation_id: str, role: str, content: str) -> Message:
        msg = Message(conversation_id=conversation_id, content=content, role=role)
        self.session.add(msg)
        await self.session.commit()
        await self.session.refresh(msg)
        return msg

    async def get_message_history(self, conversation_id: str, limit: int = 50) -> list[Message]:
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    
    async def get_history(self, conversation_id: str, limit: int = 50) -> list[Message]:
        """Alias for get_message_history"""
        return await self.get_message_history(conversation_id, limit)