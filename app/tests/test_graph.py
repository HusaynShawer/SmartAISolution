import json

from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    HumanMessage,
    SystemMessage,
)
from langchain_core.outputs import ChatGenerationChunk

from agent.graph import SupportAgentGraph


def make_graph():
    graph = SupportAgentGraph.__new__(SupportAgentGraph)
    graph.user_id = "test-user"
    return graph


def test_last_user_message():
    graph = make_graph()
    messages = [
        HumanMessage(content="first"),
        AIMessage(content="reply"),
        HumanMessage(content="second question"),
    ]

    assert graph._last_user_message(messages) == "second question"


def test_last_user_message_empty_when_no_human():
    graph = make_graph()
    messages = [SystemMessage(content="sys"), AIMessage(content="reply")]

    assert graph._last_user_message(messages) == ""


def test_route_returns_stored_intent():
    graph = make_graph()
    assert graph._route({"intent": "ticket_agent", "messages": []}) == "ticket_agent"
    assert graph._route({"intent": "banana", "messages": []}) == "respond"


def test_route_defaults_to_respond():
    graph = make_graph()
    assert graph._route({"intent": "", "messages": []}) == "respond"
    assert graph._route({"messages": []}) == "respond"


def chunk(content: str) -> ChatGenerationChunk:
    return ChatGenerationChunk(message=AIMessageChunk(content=content))


def stream_start(run_id: str, node: str) -> dict:
    return {
        "event": "on_chat_model_start",
        "run_id": run_id,
        "metadata": {"langgraph_node": node},
        "data": {},
    }


def stream_token(run_id: str, node: str, content: str) -> dict:
    return {
        "event": "on_chat_model_stream",
        "run_id": run_id,
        "metadata": {"langgraph_node": node},
        "data": {"chunk": chunk(content)},
    }


def stream_end(run_id: str, node: str, content: str = "", usage: dict | None = None) -> dict:
    if usage is not None:
        message = AIMessage(content=content, usage_metadata=usage)
    else:
        message = AIMessage(content=content)
    return {
        "event": "on_chat_model_end",
        "run_id": run_id,
        "metadata": {"langgraph_node": node},
        "data": {"output": message},
    }


class FakeGraph:
    def __init__(self, events: list[dict]) -> None:
        self._events = events

    async def astream_events(self, *args, **kwargs):
        for event in self._events:
            yield event


async def collect(graph: SupportAgentGraph) -> tuple[list[str], dict]:
    tokens: list[str] = []
    usage: dict = {}
    async for item in graph.run_stream("hello", []):
        if item.startswith("__usage__:"):
            usage = json.loads(item.split(":", 1)[1])
        else:
            tokens.append(item)
    return tokens, usage


async def test_run_stream_skips_router_and_streams_final_node():
    graph = make_graph()
    graph.graph = FakeGraph(
        [
            stream_start("router-run", "router"),
            stream_token("router-run", "router", "RESP"),
            stream_end("router-run", "router", "RESPOND"),
            stream_start("respond-run", "respond"),
            stream_token("respond-run", "respond", "Hello"),
            stream_token("respond-run", "respond", " there!"),
            stream_end(
                "respond-run",
                "respond",
                "Hello there!",
                {"input_tokens": 5, "output_tokens": 3, "total_tokens": 8},
            ),
        ]
    )

    tokens, usage = await collect(graph)

    assert tokens == ["Hello", " there!"]
    assert usage["total_tokens"] == 8


async def test_run_stream_falls_back_to_end_content_when_stream_drops():
    graph = make_graph()
    graph.graph = FakeGraph(
        [
            stream_start("router-run", "router"),
            stream_end("router-run", "router", "RESPOND"),
            stream_start("respond-run", "respond"),
            stream_end("respond-run", "respond", "Full answer text"),
        ]
    )

    tokens, usage = await collect(graph)

    assert tokens == ["Full answer text"]


async def test_run_stream_yields_nothing_when_final_node_errors():
    graph = make_graph()
    graph.graph = FakeGraph(
        [
            stream_start("router-run", "router"),
            stream_end("router-run", "router", "RESPOND"),
            stream_start("respond-run", "respond"),
            stream_end("respond-run", "respond", ""),
        ]
    )

    tokens, usage = await collect(graph)

    assert tokens == []
    assert usage["total_tokens"] == 0