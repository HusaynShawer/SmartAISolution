import logging
import re

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import StructuredTool
from sqlalchemy.ext.asyncio import AsyncSession

from agent.prompts import TICKET_AGENT_PROMPT
from agent.state import AgentState
from core.llm import get_llm
from tools.create_ticket import get_create_ticket_tool
from tools.escalate import get_escalate_tool
from tools.update_ticket import get_update_ticket_tool

logger = logging.getLogger(__name__)

_AFFIRMATIVE_RE = re.compile(
    r"^\s*(?:please\s+)?(?:yes|yep|yeah|ok(?:ay)?|ok|confirm(?:ed)?|proceed|"
    r"sure|go ahead|please do|create (?:it|the ticket)|do it|make it)"
    r"(?:[\s.!]*)$",
    re.IGNORECASE,
)

_FIELD_PREFIX = r"\s*(?:[-•\d.\u2022]\s*)*"


def _is_affirmative(text: str) -> bool:
    return bool(_AFFIRMATIVE_RE.match(text))


def _is_confirmation_ask(text: str) -> bool:
    lowered = text.lower()
    return any(
        marker in lowered
        for marker in (
            "confirm",
            "shall i create",
            "should i create",
            "would you like me to create",
            "proceed?",
            "are you sure",
        )
    )


def _extract_ticket_details(text: str) -> dict | None:
    """Parse Subject/Description/Priority out of a confirmation summary."""
    clean = re.sub(r"\*\*", "", text).replace("▪ ", "")

    subject = re.search(
        rf"(?im)^{_FIELD_PREFIX}subject\s*[:：]\s*(.+?)\s*$",
        clean,
    )
    priority = re.search(
        rf"(?im)^{_FIELD_PREFIX}priority\s*[:：]\s*(low|medium|high)",
        clean,
    )
    description = re.search(
        rf"(?ims)^{_FIELD_PREFIX}description\s*[:：]\s*(.+?)\s*"
        rf"(?:^{_FIELD_PREFIX}priority\s*[:：]|$)",
        clean,
    )

    if not (subject and priority and description):
        return None

    subject_text = re.sub(r"^[\s\-•\u2022]+", "", subject.group(1)).strip()
    description_text = re.sub(r"^[\s\-•\u2022]+", "", description.group(1)).strip()
    if not subject_text or not description_text or len(subject_text) > 200:
        return None

    return {
        "subject": subject_text,
        "description": description_text,
        "priority": priority.group(1).lower(),
    }


def _confirmed_pending_ticket(messages: list) -> dict | None:
    """If the user just confirmed a proposed ticket, return its details.

    This is a deterministic safety net: it does not rely on the LLM emitting
    a tool_call, which is flaky in multi-turn confirmation flows.
    """
    if not messages or len(messages) < 2:
        return None

    last = messages[-1]
    if not isinstance(last, HumanMessage) or not _is_affirmative(last.content):
        return None

    proposal = None
    for message in reversed(messages[:-1]):
        if isinstance(message, AIMessage):
            proposal = message
            break
        if isinstance(message, HumanMessage):
            return None
    if proposal is None or not _is_confirmation_ask(proposal.content):
        return None

    return _extract_ticket_details(proposal.content)


async def ticket_agent_node(state: AgentState, session: AsyncSession) -> dict:
    """Ticket Operations Agent using OpenRouter LLM and bound tools."""
    try:
        user_id = state.get("user_id", "")
        llm = get_llm(temperature=0.1)

        tools: list[StructuredTool] = [
            get_create_ticket_tool(session, user_id),
            get_update_ticket_tool(session, user_id),
            get_escalate_tool(session, user_id),
        ]
        llm_with_tools = llm.bind_tools(tools)

        messages = state.get("messages", [])
        if not messages:
            return {
                "messages": [
                    AIMessage(
                        content=(
                            "I can help with tickets - create new ones, "
                            "update existing ones, or escalate issues. "
                            "What do you need?"
                        )
                    )
                ],
                "intent": "ticket",
            }

        confirmed_details = _confirmed_pending_ticket(messages)
        if confirmed_details:
            logger.info(
                "Ticket Agent: direct confirmation flow for user %s: %s",
                user_id,
                confirmed_details,
            )
            result = await get_create_ticket_tool(session, user_id).ainvoke(
                confirmed_details
            )
            summary_messages: list = [
                SystemMessage(content=TICKET_AGENT_PROMPT),
            ]
            for msg in messages[-6:]:
                if isinstance(msg, (HumanMessage, AIMessage)):
                    summary_messages.append(msg)
            summary_messages.append(
                HumanMessage(
                    content=(
                        "The create_support_ticket tool has already run and "
                        f"returned: {result}. "
                        "Report this result to the user: the real ticket ID, "
                        "status, and next steps. Do not invent a ticket ID."
                    )
                )
            )
            final_response = await llm.ainvoke(summary_messages)
            return {
                "messages": [final_response],
                "intent": "ticket",
                "tool_outputs": {"actions": [str(result)]},
                "escalation_needed": False,
            }

        full_messages: list = [
            SystemMessage(content=TICKET_AGENT_PROMPT),
            SystemMessage(
                content=(
                    "ALWAYS confirm actions with the user before "
                    "creating/updating tickets."
                )
            ),
        ]
        for msg in messages[-10:]:
            if isinstance(msg, (HumanMessage, AIMessage)):
                full_messages.append(msg)

        logger.info("Ticket Agent processing for user %s", user_id)

        response = await llm_with_tools.ainvoke(full_messages)

        tool_outputs = []
        escalation_needed = False

        if hasattr(response, "tool_calls") and response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("args", {})

                logger.info("Ticket Agent calling: %s", tool_name)

                try:
                    matched_tool = next(
                        (t for t in tools if t.name == tool_name), None
                    )
                    if matched_tool is None:
                        result = f"Unknown tool: {tool_name}"
                    else:
                        result = await matched_tool.ainvoke(tool_args)
                        if tool_name == "escalate_to_human":
                            escalation_needed = True

                    tool_outputs.append(
                        ToolMessage(
                            content=str(result),
                            tool_call_id=tool_call.get("id", ""),
                        )
                    )
                except Exception as tool_error:
                    logger.error("Tool error: %s", tool_error)
                    tool_outputs.append(
                        ToolMessage(
                            content=f"Error: {str(tool_error)}",
                            tool_call_id=tool_call.get("id", ""),
                        )
                    )

            final_response = await llm.ainvoke(
                full_messages
                + [response]
                + tool_outputs
                + [
                    SystemMessage(
                        content="Summarize the ticket actions taken and next steps."
                    ),
                    HumanMessage(content="What was done and what happens next?"),
                ]
            )
            return {
                "messages": [final_response],
                "intent": "ticket",
                "tool_outputs": {"actions": [t.content for t in tool_outputs]},
                "escalation_needed": escalation_needed,
            }

        return {"messages": [response], "intent": "ticket", "tool_outputs": {}}

    except Exception as exc:
        logger.error("Ticket Agent error: %s", exc, exc_info=True)
        return {
            "messages": [
                AIMessage(
                    content=(
                        "I couldn't process your ticket request. "
                        "Please try again."
                    )
                )
            ],
            "intent": "ticket",
            "error": str(exc),
        }