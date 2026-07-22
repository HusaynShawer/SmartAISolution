from sqlalchemy.ext.asyncio import AsyncSession
from app.agent.graph import SupportAgentGraph
from memory.memory_manger import MemoryManager
from app.repositories.conversation_repo import ConversationRepository
import logging
logger = logging.getLogger(__name__)
class AgentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.memory = MemoryManager(session)
        self.conv_repo = ConversationRepository(session)

    async def process_message(self, user_id: str, conversation_id: str | None, message: str) -> dict:
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

        # Load history for context
        history = await self.memory.get_recent_history(conversation_id, limit=20)
        # Convert to LangChain message format
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        lc_messages = []
        for h in history[:-1]:  # exclude the just-saved user message (it's the new one)
            if h["role"] == "user":
                lc_messages.append(HumanMessage(content=h["content"]))
            elif h["role"] == "assistant":
                lc_messages.append(AIMessage(content=h["content"]))

        # Run agent
        agent = SupportAgentGraph(self.session, user_id)
        agent_response = await agent.run(message, lc_messages)

        # Save assistant response
        await self.memory.add_assistant_message(conversation_id, agent_response)
        logger.info(f"user message: {message}")
        logger.info(f"Agent response: {agent_response}")
        return {
            "conversation_id": conversation_id,
            "response": agent_response,
        }