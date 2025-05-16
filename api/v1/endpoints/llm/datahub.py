from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, dependencies, Response
from core.deps import get_llm_service
from core.llm import LLMService
from models.question import QuestionInput
from typing import Dict, List

start_message = """
            Você tem acesso a uma ferramenta chamada `datahub_schema_search(question: str)` que constrói uma query GraphQL para buscar datasets e suas colunas dentro do DataHub da empresa.

            ### Como usar a ferramenta:

            - Utilize **termos descritivos** relacionados a tabelas, dados ou domínios de negócio.
            - O campo de busca aceita **termos simples**, **frases**, ou **buscas compostas** com operadores como AND, OR, NOT e wildcards (como `clientes*`).
            - Exemplos de termos válidos:
            - `"clientes"`
            - `"vendas AND 2023"`
            - `"transacoes NOT canceladas"`
            - `"\"usuarios ativos\""`
            - `"clientes*"`

            ### O que você recebe:
            A ferramenta retornará:
            - Nome do dataset
            - Descrição (se houver)
            - Lista de campos do schema (nome e tipo)
            - Descrição editável de cada campo, se existir

            ### Objetivo:
            Utilize esta ferramenta sempre que quiser entender a estrutura de um dataset, descobrir tabelas relevantes ou explorar os dados disponíveis no catálogo corporativo.

            ### Exemplos de uso esperados:
            - Para responder perguntas como:
            - "Quais datasets falam sobre empréstimos?"
            - "Mostre as colunas da tabela relacionada a clientes ativos"
            - "Liste tabelas que contêm dados de faturamento"
            - Gere uma busca usando o termo apropriado e chame a ferramenta.

            Lembre-se: foque em **consultar e explorar datasets relevantes** usando termos que façam sentido no contexto dos dados corporativos.

            """

user_histories: Dict[str, List[dict]] = {}

def get_history(user_id: str) -> List[dict]:
    return user_histories.get(user_id, [])

def add_message(user_id: str, role: str, content: str):
    if user_id not in user_histories:
        user_histories[user_id] = []
        user_histories[user_id].append({"system": role, "content": start_message})
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
    
