from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from core.llm_tool_datahub import datahub_schema_search_logic_list
from langchain_core.runnables import RunnableLambda
from typing import TypedDict
import logging
import json
from langchain_ollama import ChatOllama
import tiktoken


def count_tokens_openai(messages, model="gpt-4o-mini"):
    # or none
    if messages is None or len(messages) == 0:
        return 0
    
    enc = tiktoken.encoding_for_model(model)
    num_tokens = 0
    for message in messages:
        # Cada mensagem tem role e content
        num_tokens += 4  # tokens de formatação
        for key, value in message.items():
            num_tokens += len(enc.encode(str(value)))
    num_tokens += 2  # priming
    return num_tokens

def count_words(messages):
    if messages is None or len(messages) == 0:
        return 0
    return sum(len(str(msg.get("content", "")).split()) for msg in messages)

def truncate_messages_openai_for_subject(system_prompt: dict, historico: list, user_question: dict, token_limit: int, reserve_tokens_response=2000):
    # Se o histórico estiver vazio, não há necessidade de truncar
    if not historico:
        return historico

    system_prompt_tokens = count_tokens_openai([system_prompt])
    user_question_tokens = count_tokens_openai([user_question])
    history_tokens = count_tokens_openai(historico)
    total_tokens = system_prompt_tokens + user_question_tokens + history_tokens + reserve_tokens_response
    if total_tokens <= token_limit:
        return historico
    
    # Se o total de tokens exceder o limite, reduz o histórico
    max_history_tokens = token_limit - system_prompt_tokens - user_question_tokens - reserve_tokens_response
    if max_history_tokens <= 0:
        return []
    
    # reduz o histórico para o número máximo de tokens permitido
    truncated_history = []
    # Para o metodo subject não é necessário inverter a ordem
    for message in historico:
        message_tokens = count_tokens_openai([message])
        history_tokens = count_tokens_openai(truncated_history)
        if history_tokens + message_tokens <= max_history_tokens:
            truncated_history.append(message)
        else:
            break
    # não inverte a lista de mensagens truncadas para manter a ordem original
    return truncated_history
    

def truncate_messages_openai(system_prompt: dict, historico: list, user_question: dict, assistant_message: dict, modelo: str, token_limit: int, reserve_tokens_response=2000):

    qtd_tokens_assistant_message = 0
    if assistant_message is not None:
        qtd_tokens_assistant_message = count_tokens_openai([assistant_message])

    question_tokens = (
        count_tokens_openai([system_prompt]) + 
        count_tokens_openai([user_question]) + 
        qtd_tokens_assistant_message + 
        reserve_tokens_response
        )
    
    total_tokens = count_tokens_openai(historico) + question_tokens
    
    if total_tokens <= token_limit:
        return historico

    
    max_history_tokens = token_limit - question_tokens

    if max_history_tokens <= 0:
        return []


    # reduz o histórico para o número máximo de tokens permitido
    truncated_history = []
    for message in reversed(historico):
        message_tokens = count_tokens_openai([message])
        history_tokens = count_tokens_openai(truncated_history)

        if history_tokens + message_tokens <= max_history_tokens:
            truncated_history.append(message)
        else:
            break
    # inverte a lista de mensagens truncadas para manter a ordem original
    return truncated_history.reverse()


def truncate_messages_llama(system_prompt: dict, historico: list, user_question: dict, assistant_message: dict, modelo: str, token_limit: int, reserve_tokens_response=2000):
    
    qtd_tokens_assistant_message = 0
    if assistant_message is not None:
        qtd_tokens_assistant_message = count_words([assistant_message])

    question_tokens = (
        count_words([system_prompt]) + 
        count_words([user_question]) + 
        qtd_tokens_assistant_message +
        reserve_tokens_response
        )
    
    total_tokens = count_words(historico) + question_tokens
    
    if total_tokens <= token_limit:
        return historico

    
    max_history_tokens = token_limit - question_tokens

    if max_history_tokens <= 0:
        return []
    # reduz o histórico para o número máximo de tokens permitido
    truncated_history = []
    for message in reversed(historico):
        message_tokens = count_words([message])
        history_tokens = count_words(truncated_history)
        if history_tokens + message_tokens <= max_history_tokens:
            truncated_history.append(message)
        else:
            break
    # inverte a lista de mensagens truncadas para manter a ordem original
    return truncated_history.reverse()


def truncate_history(system_prompt: dict, historico: list, user_question: dict, assistant_message: dict, modelo: str, token_limit: int, reserve_tokens_response=2000):
    
    if modelo == "gpt-4o-mini":
        return truncate_messages_openai(system_prompt, historico, user_question, assistant_message, modelo, token_limit)
    elif modelo == "llama3":
        return truncate_messages_llama(system_prompt, historico, user_question, assistant_message, modelo, token_limit)
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
    def __init__(self, model: str, api_key: str, temperature: float = 0.3, token_limit: int = 128000):
        self.model = model
        self.openai_api_key = api_key
        self.temperature = temperature
        self.token_limit = token_limit
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
            - Se você gerar algum código em SQL, deixe apenas o schema.tabela, retirando o database.
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
            Resposta: select * from captalys_analytics.d_calendario
            """
        }



        user_question = {"role": "user", "content": input}
        assistant_message = None

        historico = truncate_history(system_prompt=prompt, historico=historico, user_question=user_question, assistant_message=assistant_message, modelo=self.model, token_limit=self.token_limit)

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

        prompt = {
            "role": "system",
            "content": """
            Você é um assistente especializado em catálogo de dados e SQL.
            Sua tarefa é responder de forma clara e útil, utilizando sempre que possível o conteúdo da variável result.

            Regras:
            - Se a variável result estiver vazia, responda diretamente à pergunta do usuário com base no seu conhecimento.
            - Se a variável result não estiver vazia, utilize as informações contidas nela para construir uma resposta mais completa, detalhada e personalizada para o usuário.
            - Se a pergunta do usuário solicitar um exemplo de SQL, utilize os dados de result para montar a query, removendo o nome do database e mantendo apenas schema.tabela.
            - Sempre explique de forma didática, cite nomes de tabelas, campos ou exemplos práticos quando possível.
            - Não repita o conteúdo de result literalmente; integre as informações de forma natural na resposta.
            - Seja objetivo, evite respostas genéricas e adapte o tom para o contexto de dados corporativos.
            - Se a resposta conter codigo ou markdown, utilize sempre três crases (```) seguido da linguagem de programação correspondente (ex: ```sql) (ex: ```markdown) e finalize com três crases (```).
            - Se você gerar algum código em SQL, deixe apenas o schema.tabela, retirando o database.
            - Sempre responda em português.

            Exemplo de resposta com SQL:
            Resposta: select * from captalys_analytics.d_calendario
            """

        }

   
        user_question = {"role": "user", "content": input}
        assistant_message = {
            "role": "assistant",
            "content": str(result) if not isinstance(result, str) else result
        }

        historico = truncate_history(system_prompt=prompt, historico=historico, user_question=user_question, assistant_message=assistant_message, modelo=self.model, token_limit=self.token_limit)
        messages = [prompt] + historico + [user_question] + [assistant_message]


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

        fake_answer_response_255 = '' * 255
        reserved_answer_tokens = count_tokens_openai(fake_answer_response_255) + 500 # 500 tokens de reserva
        history_message_truncated = truncate_messages_openai_for_subject(system_prompt=system_prompt, historico=messages, user_question=user_question, token_limit=self.token_limit, reserve_tokens_response=reserved_answer_tokens)

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