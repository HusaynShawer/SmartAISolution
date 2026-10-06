from langchain_core.tools import StructuredTool
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.user_repo import UserRepository


def get_customer_info_tool(session: AsyncSession, user_id: str) -> StructuredTool:
    async def wrapper() -> str:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(user_id=user_id)
        if not user:
            return "User not found"
        return str(
            {
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role,
            }
        )

    return StructuredTool.from_function(
        name="get_customer_information",
        description="Get the current customer's account details.",
        func=wrapper,
        coroutine=wrapper,
    )