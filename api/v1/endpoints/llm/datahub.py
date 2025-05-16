from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, dependencies, Response
from core.deps import get_llm_service
from core.llm import LLMService
from models.question import QuestionInput
from typing import Dict, List
from core.configs import settings


user_histories: Dict[str, List[dict]] = {}

def get_history(user_id: str) -> List[dict]:
    return user_histories.get(user_id, [])

def add_message(user_id: str, role: str, content: str):
    if user_id not in user_histories:
        user_histories[user_id] = []
        user_histories[user_id].append({"system": role, "content": settings.START_MESSAGE})
    user_histories[user_id].append({"role": role, "content": content})

router = APIRouter(
    prefix="/datahub"
)

@router.post(
    "/"
)
async def resume_question_one_word(
    input: QuestionInput,
    llm_service: LLMService = Depends(get_llm_service),
    user_id: str = "default_user"  # Em produção, use autenticação real!
):
    
    # Adiciona a mensagem do usuário ao histórico
    add_message(user_id, "user", input.question)
    # Recupera o histórico completo
    history = get_history(user_id)
    # Usa o agente para responder com contexto
    resposta = await llm_service.ask_with_tools(history)
    # Adiciona resposta do agente ao histórico
    add_message(user_id, "assistant", resposta)
    return {"resposta": resposta["output"]}
    
