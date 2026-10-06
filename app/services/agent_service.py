import json
import logging

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import SupportAgentGraph
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.token_usage_repo import TokenUsageRepository
from core.config import settings
from core.llm import get_llm
from memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 10


class AgentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.memory = MemoryManager(session)
        self.conv_repo = ConversationRepository(session)
        self.usage_repo = TokenUsageRepository(session)

    async def process_message(
        self, user_id: str, conversation_id: str | None, message: str
    ):
        conversation_id = await self._ensure_conversation(
            user_id, conversation_id, message
        )

        await self.memory.add_user_message(conversation_id, message)
        history = await self.memory.get_recent_history(
            conversation_id, limit=MAX_HISTORY_MESSAGES
        )
        lc_messages = self._to_langchain_messages(history)

        agent = SupportAgentGraph(self.session, user_id)
        response, usage = await agent.run(message, lc_messages)

        if response:
            await self.memory.add_assistant_message(conversation_id, response)
            await self._auto_title(user_id, conversation_id, message, response)
            await self._record_usage(user_id, conversation_id, usage)

        return {"conversation_id": conversation_id, "response": response}

    async def process_message_stream(
        self, user_id: str, conversation_id: str | None, message: str
    ):
        conversation_id = await self._ensure_conversation(
            user_id, conversation_id, message
        )

        await self.memory.add_user_message(conversation_id, message)
        history = await self.memory.get_recent_history(
            conversation_id, limit=MAX_HISTORY_MESSAGES
        )
        lc_messages = self._to_langchain_messages(history)

        agent = SupportAgentGraph(self.session, user_id)
        full_response = ""
        async for token in agent.run_stream(message, lc_messages):
            if token.startswith("__usage__:"):
                usage = json.loads(token.split(":", 1)[1])
                await self._record_usage(user_id, conversation_id, usage)
                continue
            full_response += token
            yield token

        if not full_response:
            full_response = (
                "I'm having trouble reaching the AI service right now. "
                "Please try again in a moment."
            )
            yield full_response

        if full_response:
            await self.memory.add_assistant_message(conversation_id, full_response)
            await self._auto_title(user_id, conversation_id, message, full_response)

        yield f"__conversation_id__:{conversation_id}"

    async def _ensure_conversation(
        self, user_id: str, conversation_id: str | None, message: str
    ) -> str:
        if not conversation_id:
            conv = await self.conv_repo.create(user_id, title=message[:50])
            return conv.id

        conv = await self.conv_repo.get_conv_by_id(conversation_id)
        if not conv or conv.user_id != user_id:
            conv = await self.conv_repo.create(user_id)
            return conv.id
        return conv.id

    async def _record_usage(
        self, user_id: str, conversation_id: str, usage: dict
    ) -> None:
        try:
            await self.usage_repo.record(
                user_id=user_id,
                conversation_id=conversation_id,
                model=settings.LLM_MODEL,
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                cost_usd=0.0,
            )
        except Exception as exc:
            logger.warning("Failed to record token usage: %s", exc)

    async def _auto_title(
        self, user_id: str, conversation_id: str, user_message: str, response: str
    ) -> None:
        conv = await self.conv_repo.get_conv_by_id(conversation_id)
        if not conv or not conv.title or conv.title == "New conversation":
            title = await self._generate_title(user_message, response)
            await self.conv_repo.update_title(conversation_id, title)

    async def _generate_title(self, user_message: str, response: str) -> str:
        try:
            llm = get_llm(temperature=0.0)
            prompt = [
                {
                    "role": "system",
                    "content": (
                        "Generate a concise conversation title (max 8 words) "
                        "based on the user's query. Return ONLY the title."
                    ),
                },
                {"role": "user", "content": user_message},
            ]
            result = await llm.ainvoke(prompt)
            title = str(result.content).strip().strip('"')
            return title[:50] or "Conversation"
        except Exception as exc:
            logger.warning("Failed to auto-generate title: %s", exc)
            return user_message[:50]

    @staticmethod
    def _to_langchain_messages(history: list[dict]) -> list[BaseMessage]:
        messages: list[BaseMessage] = []
        for item in history[:-1]:
            role = item["role"]
            content = item["content"]
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
            elif role == "system":
                messages.append(SystemMessage(content=content))
        return messages