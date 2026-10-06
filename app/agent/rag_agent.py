import logging

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import StructuredTool
from sqlalchemy.ext.asyncio import AsyncSession

from agent.prompts import RAG_AGENT_PROMPT
from agent.state import AgentState
from core.llm import get_llm
from tools.search_docs import get_search_docs_tool

logger = logging.getLogger(__name__)


async def rag_agent_node(state: AgentState, session: AsyncSession) -> dict:
    """RAG Specialist Agent Node using OpenRouter LLM and bound tools."""
    try:
        llm = get_llm(temperature=0.1)

        tools: list[StructuredTool] = [get_search_docs_tool(session)]
        llm_with_tools = llm.bind_tools(tools)

        messages = state.get("messages", [])
        if not messages:
            return {
                "messages": [
                    AIMessage(
                        content=(
                            "I need more information to help you. What "
                            "would you like to know about our product?"
                        )
                    )
                ],
                "intent": "rag",
            }

        full_messages: list = [SystemMessage(content=RAG_AGENT_PROMPT)]
        for msg in messages[-5:]:
            if isinstance(msg, (HumanMessage, AIMessage)):
                full_messages.append(msg)

        logger.info("RAG Agent processing %d messages", len(full_messages))

        response = await llm_with_tools.ainvoke(full_messages)

        tool_outputs = []
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("args", {})

                logger.info("RAG Agent calling: %s", tool_name)

                matched_tool = next(
                    (t for t in tools if t.name == tool_name), None
                )
                if matched_tool is None:
                    result = f"Unknown tool: {tool_name}"
                else:
                    result = await matched_tool.ainvoke(tool_args)

                tool_outputs.append(
                    ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call.get("id", ""),
                    )
                )

            final_response = await llm.ainvoke(
                full_messages
                + [response]
                + tool_outputs
                + [
                    SystemMessage(
                        content=(
                            "Synthesize a clear, helpful answer from the "
                            "documentation results above."
                        )
                    ),
                    HumanMessage(content="Provide the final answer."),
                ]
            )
            return {
                "messages": [final_response],
                "intent": "rag",
                "tool_outputs": {
                    "docs": [t.content for t in tool_outputs]
                },
            }

        return {"messages": [response], "intent": "rag", "tool_outputs": {}}

    except Exception as exc:
        logger.error("RAG Agent error: %s", exc, exc_info=True)
        return {
            "messages": [
                AIMessage(
                    content=(
                        "I encountered an error searching the documentation. "
                        "Please try again."
                    )
                )
            ],
            "intent": "rag",
            "error": str(exc),
        }