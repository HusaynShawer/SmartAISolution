from sqlalchemy.ext.asyncio import AsyncSession
from app.agent.graph import SupportAgentGraph
from memory.memory_manger import MemoryManager
from app.repositories.conversation_repo import ConversationRepository
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import logging
logger = logging.getLogger(__name__)
class AgentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.memory = MemoryManager(session)
        self.conv_repo = ConversationRepository(session)

    async def process_message(self, user_id: str, conversation_id: str | None, message: str):
        # Get or create conversation
        if not conversation_id:
            conv = await self.conv_repo.create(user_id, title=message[:50])
            conversation_id = conv.id
        else:
            conv = await self.conv_repo.get_conv_by_id(conversation_id)
            if not conv or conv.user_id != user_id:
                conv = await self.conv_repo.create(user_id)
                conversation_id = conv.id

        # Save user message
        await self.memory.add_user_message(conversation_id, message)

        # Load history
        history = await self.memory.get_recent_history(conversation_id, limit=20)
        lc_messages = []
        for h in history[:-1]:
            if h["role"] == "user":
                lc_messages.append(HumanMessage(content=h["content"]))
            elif h["role"] == "assistant":
                lc_messages.append(AIMessage(content=h["content"]))
            elif h["role"] == "system":
                lc_messages.append(SystemMessage(content=h["content"]))

        # Run agent
        agent = SupportAgentGraph(self.session, user_id)
        response = await agent.run(message, lc_messages)

        # Save assistant response
        if response:
            await self.memory.add_assistant_message(conversation_id, response)

        return {"conversation_id": conversation_id, "response": response}

    async def process_message_stream(self, user_id: str, conversation_id: str | None, message: str):
            # Get or create conversation (same as before)
            if not conversation_id:
                conv = await self.conv_repo.create(user_id, title=message[:50])
                conversation_id = conv.id
            else:
                conv = await self.conv_repo.get_conv_by_id(conversation_id)
                if not conv or conv.user_id != user_id:
                    conv = await self.conv_repo.create(user_id)
                    conversation_id = conv.id

            # Save user message
            await self.memory.add_user_message(conversation_id, message)

            # Load history
            history = await self.memory.get_recent_history(conversation_id, limit=20)
            lc_messages = []
            for h in history[:-1]:
                if h["role"] == "user":
                    lc_messages.append(HumanMessage(content=h["content"]))
                elif h["role"] == "assistant":
                    lc_messages.append(AIMessage(content=h["content"]))
                elif h["role"] == "system":
                    lc_messages.append(SystemMessage(content=h["content"]))

            # Run agent and collect streamed tokens
            agent = SupportAgentGraph(self.session, user_id)
            full_response = ""
            async for token in agent.run_stream(message, lc_messages):
                full_response += token
                yield token

            # Save assistant response after streaming completes
            if full_response:
                await self.memory.add_assistant_message(conversation_id, full_response)

            # Optionally yield the conversation_id at the end (could be done via event)
            # For simplicity, we can send a final event with the ID.
            yield f"__conversation_id__:{conversation_id}"