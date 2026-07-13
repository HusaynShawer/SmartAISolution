from repositories.conversation_repo import ConversationRepository,MessageRepository
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.conversation import Conversationresponse, CnoversationDetailRespone,MessageResponse

class ConversationService:
    def __init__(self,session:AsyncSession):
        self.session = session
        self.conv_repo = ConversationRepository
        self.msg_repo  = MessageRepository

    async def create_conversation(self,user_id,title:str|None=None)->Conversationresponse:
        conv = await self.conv_repo.create(user_id=user_id,title=title)
        return Conversationresponse.model_validate(conv)
    
    async def get_user_conversations(self, user_id:str,limit:int,skip:int)->list[Conversationresponse]:
        convs = await self.conv_repo.list_conv_by_id(user_id=user_id, skip=skip, limit=limit)
        return [Conversationresponse.model_validate(c) for c in convs]
    
    async def get_coversation_detail(self, user_id:str,conv_id:str,limit:int)->CnoversationDetailRespone:
        
        conv = await self.conv_repo.get_conv_by_id(conv_id=conv_id)
        if not conv or conv.user_id !=user_id:
            return "error"
        
        msgs = await self.msg_repo.get_message_history(conversation_id=conv_id,limit=limit)
        conv_response = Conversationresponse.model_validate(conv)
        
        return CnoversationDetailRespone(**conv_response.model_dump(),
                                        messages=[MessageResponse.model_validate(msg) for msg in msgs]
                                        )
        
    async def delete_conversation(self, user_id:str,conv_id:str)->None:
        
        conv = await self.conv_repo.get_conv_by_id(conv_id=conv_id)
        if not conv or conv.user_id !=user_id:
            return "error"
        
        await self.conv_repo.delete_conv(conv_id=conv_id)