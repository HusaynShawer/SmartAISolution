from sqlalchemy.ext.asyncio import AsyncSession

from models.token_usage import TokenUsage


class TokenUsageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        user_id: str,
        conversation_id: str | None,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float = 0.0,
    ) -> TokenUsage:
        usage = TokenUsage(
            user_id=user_id,
            conversation_id=conversation_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost_usd=cost_usd,
        )
        self.session.add(usage)
        await self.session.commit()
        await self.session.refresh(usage)
        return usage
