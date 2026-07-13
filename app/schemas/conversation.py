from pydantic import BaseModel
from datetime import datetime
from typing import List

class MessageResponse(BaseModel):
    id:str
    role:str
    content:str
    created_at:datetime
    
    model_config= {"from_attributes":True}
    
class Conversationresponse(BaseModel):
    id:str
    title:str
    status:str
    created_at:datetime
    updated_at:datetime

    model_config= {"from_attributes":True}
    
class CnoversationDetailRespone(Conversationresponse):
    messages:List[MessageResponse] = []