from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    messages: list
    user_id: str
    conversation_id: str
    intent: str
    tool_outputs: dict
    final_response: str | None
    error: str | None
    escalation_needed: bool

    pending_action: dict | None