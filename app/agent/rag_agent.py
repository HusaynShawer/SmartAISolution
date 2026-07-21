import logging
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from sqlalchemy.ext.asyncio import AsyncSession

from agent.state import AgentState
from agent.prompts import RAG_AGENT_PROMPT
from tools.search_docs import get_search_docs_tool
from core.llm import get_llm

logger = logging.getLogger(__name__)


async def rag_agent_node(state: AgentState, session: AsyncSession) -> dict:
    """
    RAG Specialist Agent Node - Uses OpenRouter LLM.
    """
    try:
        # Get LLM via OpenRouter
        llm = get_llm(temperature=0.1)
        
        # Bind documentation search tool
        tools = [get_search_docs_tool(session)]
        llm_with_tools = llm.bind_tools(tools)
        
        # Extract messages from state
        messages = state.get("messages", [])
        if not messages:
            return {
                "messages": [AIMessage(content="I need more information to help you. What would you like to know about our product?")],
                "intent": "rag",
            }
        
        # Build prompt
        full_messages = [SystemMessage(content=RAG_AGENT_PROMPT)]
        for msg in messages[-5:]:
            if isinstance(msg, (HumanMessage, AIMessage)):
                full_messages.append(msg)
        
        logger.info(f"RAG Agent processing {len(full_messages)} messages")
        
        # Invoke LLM
        response = await llm_with_tools.ainvoke(full_messages)
        
        # Handle tool calls
        tool_outputs = []
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("args", {})
                
                logger.info(f"RAG Agent calling: {tool_name}")
                
                if tool_name == "search_documentation":
                    search_result = await get_search_docs_tool(session).ainvoke(tool_args)
                    tool_outputs.append(
                        ToolMessage(content=str(search_result), tool_call_id=tool_call.get("id", ""))
                    )
            
            # Synthesize final answer
            final_messages = full_messages + [response] + tool_outputs + [
                SystemMessage(content="Synthesize a clear, helpful answer from the documentation results above."),
                HumanMessage(content="Provide the final answer.")
            ]
            
            final_response = await llm.ainvoke(final_messages)
            return {"messages": [final_response], "intent": "rag", "tool_outputs": {"docs": [t.content for t in tool_outputs]}}
        
        return {"messages": [response], "intent": "rag", "tool_outputs": {}}
        
    except Exception as e:
        logger.error(f"RAG Agent error: {e}", exc_info=True)
        return {
            "messages": [AIMessage(content="I encountered an error searching the documentation. Please try again.")],
            "intent": "rag",
            "error": str(e),
        }