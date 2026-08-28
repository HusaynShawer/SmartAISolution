import logging
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from sqlalchemy.ext.asyncio import AsyncSession

from agent.state import AgentState
from app.agent.prompts import SQL_AGENT_PROMPT
from tools.get_customer_info import get_customer_info_tool
from tools.search_tickets import get_search_ticket_tool
from core.llm import get_llm

logger = logging.getLogger(__name__)


async def sql_agent_node(state: AgentState, session: AsyncSession) -> dict:
    """
    SQL / Customer Data Agent - Uses OpenRouter LLM.
    """
    try:
        user_id = state.get("user_id", "")
        llm = get_llm(temperature=0.1)
        
        tools = [
            get_customer_info_tool(session),
            get_search_ticket_tool(session, user_id),
        ]
        llm_with_tools = llm.bind_tools(tools)
        
        messages = state.get("messages", [])
        if not messages:
            return {
                "messages": [AIMessage(content="I can check your account details and ticket history. What would you like to know?")],
                "intent": "sql",
            }
        
        full_messages = [
            SystemMessage(content=SQL_AGENT_PROMPT),
            SystemMessage(content=f"Current user ID: {user_id}"),
        ]
        for msg in messages[-5:]:
            if isinstance(msg, (HumanMessage, AIMessage)):
                full_messages.append(msg)
        
        logger.info(f"SQL Agent processing for user {user_id}")
        
        response = await llm_with_tools.ainvoke(full_messages)
        
        tool_outputs = []
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name", "")
                
                logger.info(f"SQL Agent calling: {tool_name}")
                
                if tool_name == "get_customer_information":
                    result = await get_customer_info_tool(session).ainvoke({"user_id": user_id})
                elif tool_name == "search_previous_tickets":
                    result = await get_search_ticket_tool(session, user_id).ainvoke(tool_call.get("args", {}))
                else:
                    result = f"Unknown tool: {tool_name}"
                
                tool_outputs.append(
                    ToolMessage(content=str(result), tool_call_id=tool_call.get("id", ""))
                )
            
            final_response = await llm.ainvoke(
                full_messages + [response] + tool_outputs + [
                    SystemMessage(content="Summarize the account and ticket information clearly."),
                    HumanMessage(content="Provide the answer based on the data.")
                ]
            )
            return {"messages": [final_response], "intent": "sql", "tool_outputs": {"data": [t.content for t in tool_outputs]}}
        
        return {"messages": [response], "intent": "sql", "tool_outputs": {}}
        
    except Exception as e:
        logger.error(f"SQL Agent error: {e}", exc_info=True)
        return {
            "messages": [AIMessage(content="I couldn't retrieve your account information. Please try again.")],
            "intent": "sql",
            "error": str(e),
        }