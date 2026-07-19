from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    messages:Annotated[Sequence[BaseMessage],operator.add]
    user_id:str
    conversation_id:str
    intent:str
    tool_output:dict
    final_reponse:str|None
    error:str|None
    escalation_needed:bool