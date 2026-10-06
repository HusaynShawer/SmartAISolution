import json
import logging

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.outputs import ChatGenerationChunk
from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from agent.prompts import ROUTER_PROMPT, SUPERVISOR_PROMPT
from agent.rag_agent import rag_agent_node
from agent.sql_agent import sql_agent_node
from agent.state import AgentState
from agent.ticket_agent import ticket_agent_node
from core.llm import get_llm

logger = logging.getLogger(__name__)

ROUTER_OPTIONS = "RAG_AGENT, SQL_AGENT, TICKET_AGENT, or RESPOND"


class SupportAgentGraph:
    _ROUTE_MAP = {
        "rag_agent": "rag_agent",
        "sql_agent": "sql_agent",
        "ticket_agent": "ticket_agent",
        "respond": "respond",
    }

    def __init__(self, session: AsyncSession, user_id: str) -> None:
        self.session = session
        self.user_id = user_id
        self.llm = get_llm(temperature=0.1)
        self.graph = self._build_graph()

    async def router(self, state: AgentState) -> dict:
        """Router: Decides which specialist handles the request."""
        messages = state.get("messages", [])
        if not messages:
            return {"intent": "respond"}

        last_user_msg = self._last_user_message(messages)

        prompt = [
            {"role": "system", "content": ROUTER_PROMPT},
            {
                "role": "user",
                "content": f"Message: {last_user_msg}\nClassify: {ROUTER_OPTIONS}",
            },
        ]

        response = await self.llm.ainvoke(prompt)
        intent = str(response.content).strip().upper()

        mapping = {
            "RAG_AGENT": "rag_agent",
            "SQL_AGENT": "sql_agent",
            "TICKET_AGENT": "ticket_agent",
            "RESPOND": "respond",
        }

        normalized = mapping.get(intent, "respond")
        logger.info("Router: %s -> %s", intent, normalized)
        return {"intent": normalized}

    @staticmethod
    def _last_user_message(messages: list) -> str:
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                return str(msg.content)
        return ""

    def _route(self, state: AgentState) -> str:
        intent = state.get("intent", "respond")
        return intent if intent in self._ROUTE_MAP else "respond"

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
            return {
                "messages": [AIMessage(content="How can I help you today?")]
            }

        prompt = [{"role": "system", "content": SUPERVISOR_PROMPT}]
        for m in messages[-5:]:
            role = "user" if isinstance(m, HumanMessage) else "assistant"
            prompt.append({"role": role, "content": str(m.content)})

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
            {
                "rag_agent": "rag_agent",
                "sql_agent": "sql_agent",
                "ticket_agent": "ticket_agent",
                "respond": "respond",
            },
        )

        workflow.add_edge("rag_agent", END)
        workflow.add_edge("sql_agent", END)
        workflow.add_edge("ticket_agent", END)
        workflow.add_edge("respond", END)

        return workflow.compile()

    def _initial_state(self, conversation_messages: list, user_message: str) -> AgentState:
        return {
            "messages": [*conversation_messages, HumanMessage(content=user_message)],
            "user_id": self.user_id,
            "conversation_id": "",
            "intent": "",
            "tool_outputs": {},
            "final_response": None,
            "error": None,
            "escalation_needed": False,
            "pending_action": None,
        }

    async def run_stream(
        self, user_message: str, conversation_messages: list
    ):
        """Yield tokens from the final (non-router) LLM response, then usage."""
        initial_state = self._initial_state(conversation_messages, user_message)

        active_run_id: str | None = None
        yielded_tokens = False
        fallback: str | None = None
        usage: dict = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

        async for event in self.graph.astream_events(initial_state, version="v2"):
            event_type = event["event"]
            run_id = event.get("run_id")
            node = (event.get("metadata") or {}).get("langgraph_node", "")
            if node == "router":
                continue

            if event_type == "on_chat_model_stream" and run_id == active_run_id:
                chunk = event["data"]["chunk"]
                if isinstance(chunk, ChatGenerationChunk):
                    content = chunk.message.content
                    if isinstance(content, str) and content:
                        yielded_tokens = True
                        yield content
            elif event_type == "on_chat_model_start":
                active_run_id = run_id
            elif event_type == "on_chat_model_end" and run_id == active_run_id:
                generation = event["data"]["output"]
                message = getattr(generation, "message", generation)
                if isinstance(message, str):
                    message = generation
                end_content = getattr(message, "content", None)
                if isinstance(end_content, str) and end_content:
                    fallback = end_content
                metadata: dict = getattr(message, "usage_metadata", None) or {}
                usage["input_tokens"] += metadata.get("input_tokens", 0)
                usage["output_tokens"] += metadata.get("output_tokens", 0)
                usage["total_tokens"] += metadata.get("total_tokens", 0)

        if not yielded_tokens and fallback:
            yield fallback

        yield f"__usage__:{json.dumps(usage)}"

    async def run(
        self, user_message: str, conversation_messages: list
    ) -> tuple[str, dict]:
        """Run the agent graph and return the final response and token usage."""
        initial_state = self._initial_state(conversation_messages, user_message)
        result = await self.graph.ainvoke(initial_state)

        usage: dict = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        for msg in result.get("messages", []):
            if isinstance(msg, AIMessage) and msg.usage_metadata:
                usage["input_tokens"] += msg.usage_metadata.get(
                    "input_tokens", 0
                )
                usage["output_tokens"] += msg.usage_metadata.get(
                    "output_tokens", 0
                )
                usage["total_tokens"] += msg.usage_metadata.get(
                    "total_tokens", 0
                )

        for msg in reversed(result.get("messages", [])):
            if isinstance(msg, AIMessage) and msg.content:
                logger.info(
                    "LLM usage: %s tokens (in=%s out=%s)",
                    usage["total_tokens"],
                    usage["input_tokens"],
                    usage["output_tokens"],
                )
                return str(msg.content), usage

        return (
            "I apologize, I couldn't process your request. Please try again.",
            usage,
        )