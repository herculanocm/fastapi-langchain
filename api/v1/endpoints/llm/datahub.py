from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, dependencies, Response
from core.deps import get_llm_service
from core.llm import LLMService
from models.question import QuestionInput

router = APIRouter(
    prefix="/datahub"
)

@router.post(
    "/"
)
async def resume_question_one_word(
    input: QuestionInput,
    llm_service: LLMService = Depends(get_llm_service)
):
    
    resposta = await llm_service.ask_with_tools(input.question)
    return {"resposta": resposta}
    
