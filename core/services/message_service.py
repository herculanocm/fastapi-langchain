from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from models.message_model import MessageModel
from sqlmodel import select
from core.configs import settings

class MessageService:
    
    @staticmethod
    async def create(session: AsyncSession, message: MessageModel) -> MessageModel:
        session.add(message)
        await session.commit()
        await session.refresh(message)
        return message

    @staticmethod
    async def get_by_id(session: AsyncSession, id) -> Optional[MessageModel]:
        result = await session.execute(
            select(MessageModel).where(MessageModel.id == id)
        )
        return result.scalars().first()

    @staticmethod
    async def list_by_thread(session: AsyncSession, user_id: str, thread_id: str) -> List[MessageModel]:
        result = await session.execute(
            select(MessageModel)
            .where(
                MessageModel.user_id == user_id,
                MessageModel.thread_id == thread_id
            )
            .order_by(MessageModel.created_at)
        )
        return result.scalars().all()

    @staticmethod
    async def update_content(session: AsyncSession, id, new_content: str) -> Optional[MessageModel]:
        result = await session.execute(
            select(MessageModel).where(MessageModel.id == id)
        )
        message = result.first()
        if message:
            message.content = new_content
            await session.commit()
            await session.refresh(message)
        return message

    @staticmethod
    async def delete(session: AsyncSession, id) -> None:
        result = await session.execute(
            select(MessageModel).where(MessageModel.id == id)
        )
        message = result.first()
        if message:
            await session.delete(message)
            await session.commit()

    @staticmethod
    async def ensure_system_message(session: AsyncSession, user_id: str, thread_id: str):
        result = await session.execute(
            select(MessageModel)
            .where(
               (MessageModel.user_id == user_id) & (MessageModel.thread_id == thread_id) & (MessageModel.role == "system")
            )
        )
        exists = result.first()
        if not exists:

            system_message = MessageModel(
                user_id=user_id,
                thread_id=thread_id,
                role="system",
                content=settings.START_MESSAGE
            )
            session.add(system_message)
            await session.commit()
            await session.refresh(system_message)

    @staticmethod
    def to_dict_list(messages: List[MessageModel]) -> List[dict]:
        messages_sorted = sorted(messages, key=lambda m: m.created_at)
        return [{"role": m.role, "content": m.content} for m in messages_sorted]