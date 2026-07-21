import logging
from typing import Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from agent.state import AgentState
from agent.rag_agent import rag_agent_node
from agent.sql_agent import sql_agent_node
from agent.ticket_agent import ticket_agent_node
from app.agent.prompts import SUPERVISOR_PROMPT, ROUTER_PROMPT
from core.llm import get_llm

logger = logging.getLogger(__name__)


class SupportAgentGraph:
    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id
        self.llm = get_llm(temperature=0.1)
        self.graph = self._build_graph()

    async def router(self, state: AgentState) -> dict:
        """Router: Decides which specialist handles the request."""
        messages = state.get("messages", [])
        if not messages:
            return {"intent": "respond"}

        last_user_msg = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                last_user_msg = msg.content
                break

        prompt = [
            {"role": "system", "content": ROUTER_PROMPT},
            {"role": "user", "content": f"Message: {last_user_msg}\nClassify: RAG_AGENT, SQL_AGENT, TICKET_AGENT, or RESPOND"}
        ]

        response = await self.llm.ainvoke(prompt)
        intent = response.content.strip().upper()

        mapping = {
            "RAG_AGENT": "rag_agent",
            "SQL_AGENT": "sql_agent",
            "TICKET_AGENT": "ticket_agent",
            "RESPOND": "respond",
        }

        normalized = mapping.get(intent, "respond")
        logger.info(f"Router: {intent} → {normalized}")
        return {"intent": normalized}

    def _route(self, state: AgentState) -> str:
        return state.get("intent", "respond")

    async def rag_node(self, state: AgentState) -> dict:
        return await rag_agent_node(state, self.session)

    async def sql_node(self, state: AgentState) -> dict:
        return await sql_agent_node(state, self.session)

    async def ticket_node(self, state: AgentState) -> dict:
        return await ticket_agent_node(state, self.session)

    async def respond_node(self, state: AgentState) -> dict:
        """Direct response without tools."""
        messages = state.get("messages", [])
        if not messages:
            return {"messages": [AIMessage(content="How can I help you today?")]}

        prompt = [
            {"role": "system", "content": SUPERVISOR_PROMPT},
        ]
        for m in messages[-5:]:
            role = "user" if isinstance(m, HumanMessage) else "assistant"
            prompt.append({"role": role, "content": m.content})

        response = await self.llm.ainvoke(prompt)
        return {"messages": [response]}

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("router", self.router)
        workflow.add_node("rag_agent", self.rag_node)
        workflow.add_node("sql_agent", self.sql_node)
        workflow.add_node("ticket_agent", self.ticket_node)
        workflow.add_node("respond", self.respond_node)

        workflow.set_entry_point("router")

        workflow.add_conditional_edges(
            "router",
            self._route,
            {"rag_agent": "rag_agent", "sql_agent": "sql_agent", "ticket_agent": "ticket_agent", "respond": "respond"}
        )

        workflow.add_edge("rag_agent", END)
        workflow.add_edge("sql_agent", END)
        workflow.add_edge("ticket_agent", END)
        workflow.add_edge("respond", END)

        return workflow.compile()

    async def run(self, user_message: str, conversation_messages: list) -> str:
        initial_state: AgentState = {
            "messages": conversation_messages + [HumanMessage(content=user_message)],
            "user_id": self.user_id,
            "conversation_id": "",
            "intent": "",
            "tool_outputs": {},
            "final_response": None,
            "error": None,
            "escalation_needed": False,
        }

        result = await self.graph.ainvoke(initial_state)

        for msg in reversed(result.get("messages", [])):
            if isinstance(msg, AIMessage) and msg.content:
                return msg.content

        return "I apologize, I couldn't process your request. Please try again."