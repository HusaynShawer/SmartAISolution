from typing import TypedDict


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