from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from models.thread_model import ThreadMessageModel
from models.message_model import MessageModel
from schemas.thread_schema import ThreadMessageSchema
from sqlmodel import select
from core.utils import now_sp
import uuid

class ThreadService:
    
    @staticmethod
    async def create(session: AsyncSession, data: ThreadMessageSchema) -> ThreadMessageSchema:

        # Mapper de ThreadMessageSchema para ThreadMessageModel
        thread = ThreadMessageModel(
            user_id=data.user_id,
            subject=data.subject
        )

        session.add(thread)
        await session.commit()
        await session.refresh(thread)
        
        # Mapper de ThreadMessageModel para ThreadMessageSchema
        data_return = ThreadMessageSchema(
            id=thread.id,
            user_id=thread.user_id,
            created_at=thread.created_at,
            updated_at=thread.updated_at,
            subject=thread.subject
        )
        return data_return 

    @staticmethod
    async def get_by_id(session: AsyncSession, id: uuid.UUID) -> Optional[ThreadMessageSchema]:
        result = await session.execute(
            select(ThreadMessageModel).where(ThreadMessageModel.id == id)
        )
        first_result =  result.scalars().first()
        if first_result:
            return ThreadMessageSchema(
                id=first_result.id,
                user_id=first_result.user_id,
                created_at=first_result.created_at,
                updated_at=first_result.updated_at,
                subject=first_result.subject
            )
        return None

    @staticmethod
    async def list_by_user(session: AsyncSession, user_id: str) -> List[ThreadMessageSchema]:
        result = await session.execute(
            select(ThreadMessageModel)
            .where(ThreadMessageModel.user_id == user_id)
            .order_by(ThreadMessageModel.created_at)
        )
        list_result = result.scalars().all()

        list_return = []
        if list_result is not None and len(list_result) > 0:
            list_return = [
                ThreadMessageSchema(
                    id=thread.id,
                    user_id=thread.user_id,
                    created_at=thread.created_at,
                    updated_at=thread.updated_at,
                    subject=thread.subject
                ) for thread in list_result
            ]
            # Marcando a última thread como True, primeiro realizo o sort por created_at e depois marco a última como True
            list_return.sort(key=lambda x: x.created_at)
            list_return[-1].last_thread = True

        return list_return
        
    
    @staticmethod
    async def update_subject(session: AsyncSession, id: uuid.UUID, new_subject: str) -> Optional[ThreadMessageSchema]:
        result = await session.execute(
            select(ThreadMessageModel).where(ThreadMessageModel.id == id)
        )
        thread = result.scalars().first()
        if thread:
            thread.subject = new_subject
            thread.updated_at = now_sp()
            await session.commit()
            await session.refresh(thread)
            return ThreadMessageSchema(
                id=thread.id,
                user_id=thread.user_id,
                created_at=thread.created_at,
                updated_at=thread.updated_at,
                subject=thread.subject
            )
        return None
    
    @staticmethod
    async def delete(session: AsyncSession, id: uuid.UUID, force: bool) -> bool:
        # Se force for True, deleta as mensagens associadas
        if force:
            result = await session.execute(
                select(MessageModel).where(MessageModel.thread_id == id)
            )
            messages = result.scalars().all()
            for message in messages:
                await session.delete(message)
                await session.commit()
        
        result = await session.execute(
            select(ThreadMessageModel).where(ThreadMessageModel.id == id)
        )
        thread = result.scalars().first()
        if thread:
            await session.delete(thread)
            await session.commit()
            return True
        return False
    
    # check if the thread message has messages (prevent violates foreign key constraint)
    @staticmethod
    async def has_messages(session: AsyncSession, thread_id: uuid.UUID) -> bool:
        result = await session.execute(
            select(MessageModel).where(MessageModel.thread_id == thread_id)
        )
        thread = result.scalars().first()
        if thread:
            return True
        return False