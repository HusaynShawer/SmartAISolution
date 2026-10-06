from types import SimpleNamespace

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from services.agent_service import AgentService


class FakeConversationRepo:
    def __init__(self, user_id: str | None = None) -> None:
        self.default_user_id = user_id

    async def create(self, user_id: str, title: str | None = None):
        return SimpleNamespace(id="new-conv-1", user_id=user_id, title=title)

    async def get_conv_by_id(self, conv_id: str):
        if self.default_user_id is None:
            return None
        return SimpleNamespace(
            id=conv_id, user_id=self.default_user_id, title="Existing"
        )


class FakeMemory:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    async def get_recent_history(self, conversation_id: str, limit: int):
        return [m for m in self.messages]

    async def add_user_message(self, conversation_id: str, content: str) -> dict:
        self.messages.append({"role": "user", "content": content})
        return self.messages[-1]

    async def add_assistant_message(self, conversation_id: str, content: str) -> dict:
        self.messages.append({"role": "assistant", "content": content})
        return self.messages[-1]


def make_service(conversation: FakeConversationRepo) -> AgentService:
    service = AgentService.__new__(AgentService)
    service.conv_repo = conversation
    service.memory = FakeMemory()  # type: ignore[assignment]
    return service


async def test_ensure_conversation_creates_when_missing():
    service = make_service(FakeConversationRepo())
    conv_id = await service._ensure_conversation("user-1", None, "Hello")

    assert conv_id == "new-conv-1"


async def test_ensure_conversation_reuses_when_owned():
    service = make_service(FakeConversationRepo(user_id="user-1"))
    conv_id = await service._ensure_conversation("user-1", "conv-5", "Hello")

    assert conv_id == "conv-5"


async def test_ensure_conversation_creates_new_when_not_owned():
    service = make_service(FakeConversationRepo(user_id="user-2"))
    conv_id = await service._ensure_conversation("user-1", "conv-5", "Hello")

    assert conv_id == "new-conv-1"


def test_to_langchain_messages_drops_last_message_for_history():
    history = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello!"},
        {"role": "user", "content": "current question"},
    ]
    result = AgentService._to_langchain_messages(history)

    assert len(result) == 2
    assert isinstance(result[0], HumanMessage)
    assert result[0].content == "hi"
    assert isinstance(result[1], AIMessage)
    assert result[1].content == "hello!"


def test_to_langchain_messages_handles_system():
    history = [
        {"role": "system", "content": "context"},
        {"role": "user", "content": "q"},
    ]
    result = AgentService._to_langchain_messages(history)

    assert isinstance(result[0], SystemMessage)
    assert result[0].content == "context"