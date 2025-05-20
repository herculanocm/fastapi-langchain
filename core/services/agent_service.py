from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from core.llm_tool_datahub import datahub_schema_search_logic_list
from langchain_core.runnables import RunnableLambda
from typing import TypedDict, List, Union
from langchain_core.messages import BaseMessage
import re 

class AgentState(TypedDict, total=False):
    input: str
    historico: list
    action: str
    action_input: str
    result: str
    response: str

class AsyncAgentService:
    def __init__(self, model: str, api_key: str, temperature: float = 0.7):
        self.model = model
        self.openai_api_key = api_key
        self.temperature = temperature
        self.client = ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            temperature=temperature
        )

    # Nó LLM que interpreta a ação necessária
    async def llm_node(self, state: AgentState) -> AgentState:
        historico = state.get("historico", [])
        input = state.get("input", "")

        # promp especifico para o LLM com saida padronizada
        prompt = {
        "role": "system",
        "content": """
            Você é um assistente especializado em encontrar datasets e suas colunas no DataHub da empresa.

            Você tem acesso à seguinte ferramenta:
            - datahub_schema_search(question: str): busca datasets e campos no DataHub com base no termo de busca fornecido.

            ### Como usar a ferramenta:
            - Use termos descritivos relacionados a tabelas, colunas, TAGs, dados ou domínios de negócio.
            - O campo de busca aceita termos simples, frases, ou buscas compostas com AND, OR, NOT e wildcards (ex: clientes*).
            - Exemplos de termos válidos: "clientes", "vendas AND 2023", "transacoes NOT canceladas", "\"usuarios ativos\"", "clientes*".

            ### Formato de resposta:
            - Se precisar usar a ferramenta, responda exatamente assim:
            action: datahub_schema_search
            action_input: <termo de busca>
            - Se não precisar usar a ferramenta, responda diretamente ao usuário, sem action ou action_input.

            ### Exemplos:
            Usuário: "Quais datasets falam sobre empréstimos?"
            Resposta:
            action: datahub_schema_search
            action_input: empréstimos

            Usuário: "Explique o que é liquidação."
            Resposta:
            Liquidação é o processo de...

            Nunca invente uma action que não existe. Só use action se for realmente usar a ferramenta datahub_schema_search.
            Responda sempre em português.
            """
        }

        # Adiciona o prompt ao inicio do histórico
        historico = [prompt] + historico
        # Adiciona a mensagem do usuário ao histórico
        historico.append({"role": "user", "content": input})

        response = await self.client.ainvoke(historico)
        # Adaptação para AIMessage ou objeto com .content
        if hasattr(response, "content"):
            response_str = response.content
        elif isinstance(response, str):
            response_str = response
        elif isinstance(response, dict):
            response_str = response.get("content", "")
        else:
            response_str = str(response)

        parsed = self.parse_llm_response(response_str)
        state["response"] = response_str
        state["action"] = parsed["action"]
        state["action_input"] = parsed["action_input"]
        return state
    
    def parse_llm_response(self, response_str: str) -> dict:
        """
        Extrai 'action' e 'action_input' de uma string no formato:
        'action: datahub_schema_search\naction_input: liquidação'
        """
        action_match = re.search(r'action:\s*(.*)', response_str)
        action_input_match = re.search(r'action_input:\s*(.*)', response_str)
        action = action_match.group(1).strip() if action_match else "none"
        action_input = action_input_match.group(1).strip() if action_input_match else ""
        return {"action": action, "action_input": action_input}
    
    # Nó de ação que executa a ação necessária
    async def action_node_datahub_schema_search(self, state: AgentState) -> AgentState:
        action = state.get("action")
        action_input = state.get("action_input")

        if action == "datahub_schema_search":
            result = await datahub_schema_search_logic_list(action_input)
            state["result"] = result
            pass
        else:
            state["result"] = "none"
        
        return state
    
    # Nó de finalização que processa o resultado com a mensagem final para o usuário utilizando LLM
    async def anwser_node(self, state: AgentState) -> AgentState:
        historico = state.get("historico", [])
        input = state.get("input", "")
        result = state.get("result", "")

        prompt = {
            "role": "system",
            "content": """
            Você é um assistente especializado em catálogo de dados e SQL.
            Sua tarefa é responder de forma clara, útil e em português, utilizando sempre que possível o conteúdo da variável result.

            - Se a variável result estiver vazia, responda diretamente à pergunta do usuário com base no seu conhecimento.
            - Se a variável result não estiver vazia, utilize as informações contidas nela para construir uma resposta mais completa, detalhada e personalizada para o usuário.
            - Se a pergunta do usuário solicitar um exemplo de SQL, utilize os dados de result para montar a query, removendo o nome do database e mantendo apenas schema.tabela.
            - Sempre explique de forma didática, cite nomes de tabelas, campos ou exemplos práticos quando possível.
            - Não repita o conteúdo de result literalmente; integre as informações de forma natural na resposta.
            - Seja objetivo, evite respostas genéricas e adapte o tom para o contexto de dados corporativos.
            """
        }

        # Adiciona o prompt ao inicio do histórico
        historico = [prompt] + historico
        # Adiciona a mensagem do usuário ao histórico
        historico.append({"role": "user", "content": input})
        # Adiciona o resultado da busca ao histórico
        historico.append({
            "role": "assistant",
            "content": str(result) if not isinstance(result, str) else result
        })

        response = await self.client.ainvoke(historico)
           # Captura o conteúdo do AiMessage ou trata possíveis erros
        if hasattr(response, "content"):
            state["response"] = response.content
        elif isinstance(response, str):
            state["response"] = response
        elif isinstance(response, dict):
            state["response"] = response.get("content", "")
        else:
            state["response"] = str(response)
        return state
    
    async def run(self, input: str, historico: list) -> str:
        """
        Executa o agente com o input e histórico fornecidos.
        """

        state: AgentState = {
            "input": input,
            "historico": historico or [],
            "action": "",
            "action_input": "",
            "result": "",
            "response": ""
        }

        builder = StateGraph(AgentState)
        builder.add_node("llm_node", RunnableLambda(self.llm_node))
        builder.add_node("action_node_datahub_schema_search", RunnableLambda(self.action_node_datahub_schema_search))
        builder.add_node("anwser_node", RunnableLambda(self.anwser_node))

        builder.add_conditional_edges(
        "llm_node",
            lambda state: state["action"],  # <- função de roteamento
            {
                "datahub_schema_search": "action_node_datahub_schema_search",
                "none": "anwser_node"
            }
        )
        builder.add_edge("action_node_datahub_schema_search", "anwser_node")
        builder.add_edge("anwser_node", END)

        builder.set_entry_point("llm_node")
        #builder.set_finish_point(END)

        graph = builder.compile()
        state_final = await graph.ainvoke(state)
        return state_final["response"]

    # Bypass para metodo close
    async def close(self):
        pass