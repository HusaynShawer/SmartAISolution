import logging
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from sqlalchemy.ext.asyncio import AsyncSession

from agent.state import AgentState
from agent.prompts import TICKET_AGENT_PROMPT
from tools.create_ticket import get_create_ticket_tool
from tools.update_ticket import get_update_ticket_tool
from tools.escalate import get_escalate_tool
from core.llm import get_llm

logger = logging.getLogger(__name__)


async def ticket_agent_node(state: AgentState, session: AsyncSession) -> dict:
    """
    Ticket Operations Agent - Uses OpenRouter LLM.
    """
    try:
        user_id = state.get("user_id", "")
        llm = get_llm(temperature=0.1)
        
        tools = [
            get_create_ticket_tool(session, user_id),
            get_update_ticket_tool(session, user_id),
            get_escalate_tool(session, user_id),
        ]
        llm_with_tools = llm.bind_tools(tools)
        
        messages = state.get("messages", [])
        if not messages:
            return {
                "messages": [AIMessage(content="I can help with tickets - create new ones, update existing ones, or escalate issues. What do you need?")],
                "intent": "ticket",
            }
        
        full_messages = [
            SystemMessage(content=TICKET_AGENT_PROMPT),
            SystemMessage(content="ALWAYS confirm actions with the user before creating/updating tickets."),
        ]
        for msg in messages[-10:]:
            if isinstance(msg, (HumanMessage, AIMessage)):
                full_messages.append(msg)
        
        logger.info(f"Ticket Agent processing for user {user_id}")
        
        response = await llm_with_tools.ainvoke(full_messages)
        
        tool_outputs = []
        escalation_needed = False
        
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("args", {})
                
                logger.info(f"Ticket Agent calling: {tool_name}")
                
                try:
                    if tool_name == "create_support_ticket":
                        result = await get_create_ticket_tool(session, user_id).ainvoke(tool_args)
                    elif tool_name == "update_support_ticket":
                        result = await get_update_ticket_tool(session, user_id).ainvoke(tool_args)
                    elif tool_name == "escalate_to_human":
                        result = await get_escalate_tool(session, user_id).ainvoke(tool_args)
                        escalation_needed = True
                    else:
                        result = f"Unknown tool: {tool_name}"
                    
                    tool_outputs.append(
                        ToolMessage(content=str(result), tool_call_id=tool_call.get("id", ""))
                    )
                except Exception as tool_error:
                    logger.error(f"Tool error: {tool_error}")
                    tool_outputs.append(
                        ToolMessage(content=f"Error: {str(tool_error)}", tool_call_id=tool_call.get("id", ""))
                    )
            
            final_response = await llm.ainvoke(
                full_messages + [response] + tool_outputs + [
                    SystemMessage(content="Summarize the ticket actions taken and next steps."),
                    HumanMessage(content="What was done and what happens next?")
                ]
            )
            return {
                "messages": [final_response],
                "intent": "ticket",
                "tool_outputs": {"actions": [t.content for t in tool_outputs]},
                "escalation_needed": escalation_needed,
            }
        
        return {"messages": [response], "intent": "ticket", "tool_outputs": {}}
        
    except Exception as e:
        logger.error(f"Ticket Agent error: {e}", exc_info=True)
        return {
            "messages": [AIMessage(content="I couldn't process your ticket request. Please try again.")],
            "intent": "ticket",
            "error": str(e),
        }