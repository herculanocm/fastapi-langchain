from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from core.llm_tool_datahub import datahub_schema_search_logic_list
from langchain_core.runnables import RunnableLambda
from typing import TypedDict
import core.services.openai_agent_utils as openai_utils
import core.services.llama_agent_utils as llama_utils
import core.services.agent_utils as agent_utils
import logging
import json



def truncate_history(system_prompt: dict, historico: list, user_question: dict, assistant_message: dict, modelo: str, token_limit: int, reserve_tokens_response: int):
    
    if modelo == "gpt-4o-mini":
        return openai_utils.truncate_messages_openai_v2(system_prompt, historico, user_question, assistant_message, modelo, token_limit, reserve_tokens_response=reserve_tokens_response)
    elif modelo == "llama3":
        return llama_utils.truncate_messages_llama(system_prompt, historico, user_question, assistant_message, modelo, token_limit, reserve_tokens_response=reserve_tokens_response)
    else:
        raise ValueError(f"Modelo {modelo} não suportado para truncamento de mensagens.")


class AgentState(TypedDict, total=False):
    input: str
    historico: list
    action: str
    action_input: str
    result: str
    response: str

class AsyncAgentService:
    def __init__(
            self, 
            model: str, 
            api_key: str, 
            temperature: float,
            token_limit: int,
            answer_limit: int
            ):
        self.model = model
        self.openai_api_key = api_key
        self.temperature = temperature
        self.token_limit = token_limit
        self.answer_limit = answer_limit
        self.client = ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            temperature=temperature
        )
        # self.client = ChatOllama(
        #     model='llama3',
        #     temperature=0,
        # )

    # Nó LLM que interpreta a ação necessária
    async def llm_node(self, state: AgentState) -> AgentState:
        logging.info("Entrou no nó de LLM (llm_node)")
        historico = state.get("historico", [])
        input = state.get("input", "")

        logging.debug(f"Histórico recebido: {historico}")
        logging.debug(f"Input recebido: {input}")

        # promp especifico para o LLM com saida padronizada
        prompt = {
        "role": "system",
        "content": """
            Você é um assistente especializado em catálogo de dados e SQL.
            Sua tarefa é escolher entre responder ao usuário utilizando o histórico ou não. Atenção se a pergunta é sobre o catalogo de dados da empresa 
            responda com {"action": "datahub_schema_search","action_input": "*termo*"} para utilizar a ferramenta de procura de dados.

            Regras:
            - Analise cuidadosamente a mensaguem e seu histórico.
            - Se a pergunta é sobre datasets, tabelas, colunas, tags ou qualquer informação sobre o catalogo de dados da empresa, responda **exatamente** com: {"action": "datahub_schema_search","action_input": "*termo*"} se não puder responder com o histórico de mensaguens.
            - Se o histórico não contiver informações relevantes, estiver incompleto, confuso ou não permitir uma resposta clara e concisa, responda **exatamente** com: {"action": "datahub_schema_search","action_input": "*termo*"}.
            - Se o histórico contiver informações relevantes, mas ainda insuficientes para uma resposta direta, responda **exatamente** com: {"action": "datahub_schema_search","action_input": "*termo*"}.
            - Se é uma nova pergunta, responda **exatamente** com: {"action": "datahub_schema_search","action_input": "*termo*"}.
            - Se o histórico contiver informações claras, completas e diretamente relacionadas à pergunta do usuário, utilize-as para responder de forma objetiva e útil.
            - Nunca invente uma Action que não existe. Só use {"action": "datahub_schema_search","action_input": "*termo*"} quando realmente necessário.
            - Não tente responder ao usuário se não tiver certeza do ele está perguntando ou de que o histórico é suficiente.
            - Se a resposta conter codigo ou markdown, utilize sempre três crases (```) seguido da linguagem de programação correspondente (ex: ```sql) (ex: ```markdown) e finalize com três crases (```).
            - Se o usuário fizer uma pergunta que não seja sobre o catálogo de dados, responda que o seu proposito é ajudar com dados e que ele deve fazer perguntas relacionadas a datasets, tabelas, colunas, tags ou informações sobre o catálogo de dados da empresa.
            - Sempre responda em português.

            Como extrair o campo *termo* de busca:
            - O termo é uma query de graphQL que busca por datasets e campos no DataHub com base no termo de busca fornecido.
            - Use termos descritivos relacionados a tabelas, colunas, TAGs, dados ou domínios de negócio.
            - O campo de busca aceita termos simples, frases, ou buscas compostas com AND, OR, NOT e wildcards (ex: clientes*).
            - Exemplos de termos válidos: "clientes", "vendas AND 2023", "transacoes NOT canceladas", "\"usuarios ativos\"", "clientes*".

            Exemplos:
            Usuário: "Quais datasets falam sobre empréstimos?"
            Resposta: {"action": "datahub_schema_search","action_input": "emprestimos"}

            Usuário: "Quais datasets falam sobre estoque da administradora daycoval?"
            Resposta: {"action": "datahub_schema_search","action_input": "estoque AND daycoval"}

            Usuário: "Quais tabelas tenho a informação de liquidação que traga o valor do pdd para administradora singulare com data filtrada para dia 23/05/2020?"
            Resposta: {"action": "datahub_schema_search","action_input": "liquidacao"}

            Usuário: "Explique o que é liquidação."
            Resposta: Liquidação é o processo de...

            Exemplo de resposta com SQL:
            # Remova o database e mantenha apenas schema.tabela (datalake_dw.captalys_analytics.d_calendario)
            ```sql
            select * from captalys_analytics.d_calendario
            ```
            """
        }



        user_question = {"role": "user", "content": input}
        assistant_message = None

        historico = truncate_history(system_prompt=prompt, historico=historico, user_question=user_question, assistant_message=assistant_message, modelo=self.model, token_limit=self.token_limit, reserve_tokens_response=self.answer_limit)

        # Adiciona o prompt ao inicio do histórico
        messages = [prompt] + historico + [user_question]

        response = await self.client.ainvoke(messages)
        logging.debug(f"Resposta do LLM: {response}")
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
        logging.debug(f"Parsed LLM response: {parsed}")
        state["response"] = response_str
        state["action"] = parsed["action"]
        state["action_input"] = parsed["action_input"]
        return state

    def parse_llm_response(self, response_str: str) -> dict:
        logging.debug(f"Parsing LLM response string: {response_str}")
        """
        Extrai 'action' e 'action_input' de uma string no formato:
        'action: datahub_schema_search\naction_input: liquidação'
        """
        # Se response começar com {, então é um json
        if response_str.startswith("{"):
            try:
                response = json.loads(response_str)
                logging.debug(f"LLM response parsed as JSON: {response}")
                return response
            except Exception as e:
                logging.error(f"Erro ao fazer parse do JSON: {e}")

        response = {
            "action": "none",
            "action_input": "",
            "response": response_str
        }
        return response
    
    # Nó de ação que executa a ação necessária
    async def action_node_datahub_schema_search(self, state: AgentState) -> AgentState:
        logging.info("Entrou no nó de ação (action_node_datahub_schema_search)")
        action = state.get("action")
        action_input = state.get("action_input")
        logging.debug(f"Action: {action}, Action Input: {action_input}")
        if action == "datahub_schema_search":
            result = await datahub_schema_search_logic_list(action_input)
            state["result"] = result
            logging.debug(f"Resultado da busca datahub_schema_search: {result}")
        else:
            state["result"] = "none"
            logging.debug("Ação não reconhecida, result setado para 'none'")
        return state
    
    # Nó de finalização que processa o resultado com a mensagem final para o usuário utilizando LLM
    async def anwser_node(self, state: AgentState) -> AgentState:
        logging.info("Entrou no nó de resposta final (anwser_node)")
        historico = state.get("historico", [])
        input = state.get("input", "")
        result = state.get("result", "")
        logging.debug(f"Input: {input}, Result: {result}")

        system_prompt = {
            "role": "system",
            "content": """
            Você é um assistente especializado em catálogo de dados e SQL.
            Sua tarefa é responder de forma clara e útil, utilizando sempre que possível o conteúdo da variável result.

            Regras:
            - Analise cuidadosamente a mensaguem e seu histórico.
            - Analise o conteúdo adicional caso haja com role assistant anexado.
            - Se a pergunta do usuário solicitar um exemplo de SQL, utilize os dados de result para montar a query, removendo o nome do database e mantendo apenas schema.tabela.
            - Sempre explique de forma didática, cite nomes de tabelas, campos ou exemplos práticos quando possível.
            - Seja objetivo, evite respostas genéricas e adapte o tom para o contexto de dados corporativos.
            - Se a resposta conter codigo ou markdown, utilize sempre três crases (```) seguido da linguagem de programação correspondente (ex: ```sql) (ex: ```markdown) e finalize com três crases (```).
            - Sempre responda em português.

            Exemplo de resposta com SQL:
            # Remova o database e mantenha apenas schema.tabela (datalake_dw.captalys_analytics.d_calendario)
            ```sql
            select * from captalys_analytics.d_calendario
            ```
            """

        }

   
        user_question = {"role": "user", "content": input}
        assistant_message = {
            "role": "assistant",
            "content": agent_utils.compress_json_array_to_string(result)
        }

        historico = truncate_history(system_prompt=system_prompt, historico=historico, user_question=user_question, assistant_message=assistant_message, modelo=self.model, token_limit=self.token_limit, reserve_tokens_response=self.answer_limit)
        messages = [system_prompt] + historico + [user_question] + [assistant_message]


        response = await self.client.ainvoke(messages)
        logging.debug(f"Resposta final do LLM: {response}")
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
        logging.info("Iniciando execução do agente (run)")
        state: AgentState = {
            "input": input,
            "historico": historico or [],
            "action": "",
            "action_input": "",
            "result": "",
            "response": ""
        }
        logging.debug(f"Estado inicial: {state}")
        builder = StateGraph(AgentState)
        builder.add_node("llm_node", RunnableLambda(self.llm_node))
        builder.add_node("action_node_datahub_schema_search", RunnableLambda(self.action_node_datahub_schema_search))
        builder.add_node("anwser_node", RunnableLambda(self.anwser_node))
        builder.add_conditional_edges(
            "llm_node",
            lambda state: state["action"],
            {
                "datahub_schema_search": "action_node_datahub_schema_search",
                "none": END
            }
        )
        builder.add_edge("action_node_datahub_schema_search", "anwser_node")
        builder.add_edge("anwser_node", END)
        builder.set_entry_point("llm_node")
        graph = builder.compile()
        state_final = await graph.ainvoke(state)
        logging.info(f"Estado final: {state_final}")
        logging.info(f"Action final: {state_final.get('action')}")
        logging.info(f"Action input final: {state_final.get('action_input')}")
        return state_final["response"]
    
    async def resume_messages_to_subject(self, messages: list) -> str:
        logging.info("Resumindo mensagens para assunto (resume_messages_to_subject)")
        # Resumir as mensagens para criar um assunto
        system_prompt = {
            "role": "system",
            "content": """
                Você é um assistente especializado em resumo de mensagens.
                Sua tarefa é resumir as mensagens fornecidas e criar um assunto claro e conciso.

                Regras:
                - Analise cuidadosamente o conteúdo das mensagens.
                - Crie um resumo claro e conciso que capture os principais pontos discutidos.
                - O assunto deve ser curto, direto e refletir o conteúdo das mensagens.
                - O resumo deve ser no maximo 255 caracteres.
                - Sempre responda em português.
                - A sua resposta deve conter apenas o assunto, sem explicações adicionais.
                - Se não houver mensagens, responda com "Sem assunto".
            """
        }
        user_question = {"role": "user", "content": "Crie um assunto para as mensagens abaixo:"}

        fake_answer_response_255 = 'Resposta fake de exemplo com 255 caracteres para teste de truncamento, gerando um assunto claro e conciso que capture os principais pontos discutidos nas mensagens fornecidas, garantindo que o assunto seja curto e direto ao ponto.'
        fake_answer_dict = {
            "role": "assistant",
            "content": fake_answer_response_255
            }
        reserved_answer_tokens =  openai_utils.count_tokens_openai(messages=[fake_answer_dict], model=self.model) + 500 # 500 tokens de reserva
        history_message_truncated = openai_utils.truncate_messages_openai_for_subject(system_prompt=system_prompt, historico=messages, user_question=user_question, token_limit=self.token_limit, reserve_tokens_response=reserved_answer_tokens, model=self.model)

        # Adicionando ao user_question o histórico truncado
        user_question["content"] = user_question["content"] + "\n" + str(history_message_truncated)

        # Adiciona o prompt ao inicio do histórico
        prompt_messages = [system_prompt] + [user_question]

        response = await self.client.ainvoke(prompt_messages)
        logging.debug(f"Resposta final do LLM: {response}")

        if hasattr(response, "content"):
            return response.content
        elif isinstance(response, str):
            return response
        elif isinstance(response, dict):
            return response.get("content", "")
        else:
            return 'Novo assunto'


    # Bypass para metodo close
    async def close(self):
        logging.info("Fechando AsyncAgentService (close)")
        pass