from fastapi import APIRouter, Depends
from core.deps import get_llm_service, get_session
from core.llm import LLMService
from models.question import QuestionInput
from sqlalchemy.ext.asyncio import AsyncSession
from core.services.message_service import MessageService
from models.message_model import MessageModel


router = APIRouter(
    prefix="/datahub"
)

@router.post(
    "/"
)
async def chat_question(
    input: QuestionInput,
    llm_service: LLMService = Depends(get_llm_service),
    session: AsyncSession = Depends(get_session),
    thread_id: str = "default_thread"  # Em produção, use autenticação real!
):
    
    # await MessageService.ensure_system_message(session, user_id, thread_id)

    # await MessageService.create(
    #     session,
    #     MessageModel(
    #         user_id=user_id,
    #         thread_id=thread_id,
    #         role="user",
    #         content=input.question
    #     )
    # )

    # history_message_model = await MessageService.list_by_thread(session, user_id, thread_id)

    # lls_history_messages = MessageService.to_dict_list(history_message_model)
    # resposta = await llm_service.ask_with_tools(lls_history_messages)

    # # Adiciona resposta do agente ao histórico

    # await MessageService.create(
    #     session,
    #     MessageModel(
    #         user_id=user_id,
    #         thread_id=thread_id,
    #         role="assistant",
    #         content=resposta["output"]
    #     )
    # )

    return {"resposta": resposta["output"]}
    
