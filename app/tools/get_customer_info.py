from langchain_core.tools import StructuredTool
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.user_repo import UserRepository

async def get_customer_info_func(user_id:str, session:AsyncSession)->dict:
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id=user_id)
    if not user:
        return {"error":"user not found"}
    return{
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
    }

def get_customer_info_tool(session:AsyncSession):
    async def wrapper(user_id:str)->str:
        info = await get_customer_info_func(user_id,session)
        return str(info)
    return StructuredTool.from_function(
          name="get_customer_information",
        description="Get customer details by user ID. Input: user ID string.",
        func=wrapper,
        coroutine=wrapper,
    )