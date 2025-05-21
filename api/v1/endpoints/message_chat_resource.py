from fastapi import APIRouter, Depends
from core.deps import get_llm_service, get_session, get_async_agent_service
from core.llm import LLMService
from core.services.aync_agent_service import AsyncAgentService
from models.question import QuestionInput
from sqlalchemy.ext.asyncio import AsyncSession
from core.services.message_service import MessageService
from schemas.message_schema import MessageSchema

router = APIRouter(
    tags=["Chat"],
)

@router.post(
    "/chat/question",
    summary="Chat with LLM",
)
async def chat_question(
    input: QuestionInput,
    llm_service: LLMService = Depends(get_llm_service),
    session: AsyncSession = Depends(get_session),
    thread_id: str = "default_thread"  # Em produção, use autenticação real!
):
    
    await MessageService.ensure_system_message(session, thread_id)

    await MessageService.create(
        session=session,
        data=MessageSchema(
            thread_id=thread_id,
            role="user",
            content=input.question
        )
    )


    history_message_model = await MessageService.list_by_thread_id(session=session, thread_id=thread_id)

    lls_history_messages = MessageService.to_dict_list(history_message_model)
    resposta = await llm_service.ask_with_tools(lls_history_messages)

    # # Adiciona resposta do agente ao histórico

    await MessageService.create(
        session=session,
        data=MessageSchema(
            thread_id=thread_id,
            role="assistant",
            content=resposta["output"]
        )
    )

    return {"resposta": resposta["output"]}

@router.post(
    "/chat/question-graph",
    summary="Chat with LLM and Graph",
)
async def chat_question(
    input: QuestionInput,
    async_agent_service: AsyncAgentService = Depends(get_async_agent_service),
    session: AsyncSession = Depends(get_session)
):
    
    resposta = await async_agent_service.run(input.question, [])
    return {"resposta": resposta}