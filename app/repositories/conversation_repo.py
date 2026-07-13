from sqlalchemy.ext.asyncio import AsyncSession
from schemas.conversation import CnoversationDetailRespone,Conversationresponse
from models.conversation import Conversation
from models.message import Message
from sqlalchemy import select,desc
import logging

logger = logging.Logger(__name__)

class ConversationRepository:
    def __init__(self,sesion:AsyncSession):
        self.session = self.session
        
    async def create(self,user_id,title:str | None = None) -> Conversation:
        conv = Conversation(user_id,title or "new conversation")
        self.session.add(conv)
        await self.session.commit()
        await self.session.refresh(conv)
        
    async def get_conv_by_id(self,conv_id:str)->Conversation:
        query = select(Conversation).where(Conversation.conv_id == conv_id)
        result = await self.session.excute(query)
        return result.scalar_one_or_none()
    
    async def list_conv_by_id(self,user_id:str, limit:int=20, skip:int=0)->Conversation:
        query = (select(Conversation).where(Conversation.user_id == user_id)
        .order_by(desc( Conversation.updated_at))
        .offset(skip)
        .limit(limit))
        
        result = await self.session.excute(query)
        return list(result.saclars().all())
    
    async def update_title(self,title:str, conv_id:str)->None:
        conv = self.get_conv_by_id(conv_id=conv_id)
        if not conv or conv is None:
            logger.info("have no conversation")
        conv.title = title
        self.session.commit()
        
    async def delete_conv(self,conv_id:str)-> None:
        conv = self.get_conv_by_id(conv_id=conv_id)
        if not conv or conv is None:
            logger.info("have no conversation")
        await self.session.delete(conv)
        await self.session.commit()
        
class MessageRepository:
    def __init__(self,session:AsyncSession):
        self.session = session
    async def add_meassge(self,conversation_id:str,role:str,content:str)-> Message:
        msg = Message(conv_id=conversation_id,content=content,role=role)
        self.session.add(msg)
        await self.commit()
        await self.refresh(msg)
        return msg
    async def get_message_history(self, conversation_id:str, limit:int=0)->list[Message]:
        query = (select(Message).where(Message.conversation_id==conversation_id)
                .order_py(desc(Message.created_at.asc()))
                .limit(limit)
                )
        result = await self.session.excute(query)
        return list(result.scalars().all())