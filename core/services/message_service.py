from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from models.message_model import MessageModel
from schemas.message_schema import MessageSchema
from core.configs import settings
from sqlmodel import select
from core.utils import now_sp
import uuid

class MessageService:
    
    @staticmethod
    async def create(session: AsyncSession, data: MessageSchema) -> MessageSchema:
        # Mapper de MessageSchema para MessageModel

        message = MessageModel(
            thread_id=data.thread_id,
            role=data.role,
            content=data.content
        )

        session.add(message)
        await session.commit()
        await session.refresh(message)
        
        # Mapper de MessageModel para MessageSchema
        data_return = MessageSchema(
            id=message.id,
            thread_id=message.thread_id,
            role=message.role,
            created_at=message.created_at,
            content=message.content
        )
        return data_return

    @staticmethod
    async def get_by_id(session: AsyncSession, id: uuid.UUID) -> Optional[MessageSchema]:
        result = await session.execute(
            select(MessageModel).where(MessageModel.id == id)
        )
        first_result = result.scalars().first()
        if first_result:
            return MessageSchema(
                id=first_result.id,
                thread_id=first_result.thread_id,
                role=first_result.role,
                created_at=first_result.created_at,
                content=first_result.content
            )
        return None

    @staticmethod
    async def list_by_thread_id(session: AsyncSession, thread_id: uuid.UUID) -> List[MessageModel]:
        result = await session.execute(
            select(MessageModel)
            .where(
                MessageModel.thread_id == thread_id
            )
            .order_by(MessageModel.created_at)
        )
        list_result = result.scalars().all()
        return [
            MessageSchema(
                id=message.id,
                thread_id=message.thread_id,
                role=message.role,
                created_at=message.created_at,
                content=message.content
            )
            for message in list_result
        ]


    @staticmethod
    async def delete(session: AsyncSession, id: uuid.UUID) -> bool:
        result = await session.execute(
            select(MessageModel).where(MessageModel.id == id)
        )
        message = result.scalars().first()
        if message:
            await session.delete(message)
            await session.commit()
            return True
        return False

    @staticmethod
    async def ensure_system_message(session: AsyncSession, thread_id: uuid.UUID):
        result = await session.execute(
            select(MessageModel)
            .where(
               (MessageModel.thread_id == thread_id) & (MessageModel.role == "system")
            )
        )
        exists = result.scalars().first()
        if not exists:

            system_message = MessageModel(
                thread_id=thread_id,
                role="system",
                content=settings.START_MESSAGE
            )
            system_message.created_at = now_sp()
            session.add(system_message)
            await session.commit()
            await session.refresh(system_message)

    @staticmethod
    def to_dict_list(messages: List[MessageModel]) -> List[dict]:
        messages_sorted = sorted(messages, key=lambda m: m.created_at)
        return [{"role": m.role, "content": m.content} for m in messages_sorted]