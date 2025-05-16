from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent, initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from core.llm_tool_datahub import datahub_schema_search_logic,datahub_schema_search
from langchain.prompts import ChatPromptTemplate

class LLMService:
    def __init__(self, model: str, api_key: str, temperature: float = 0.7):
        self.model = model
        self.openai_api_key = api_key
        self.temperature = temperature
        self.client = ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            temperature=temperature
        )

        self.agent_executor: AgentExecutor | None = None

    async def init_agent(self):
        if self.agent_executor is None:
            '''
            chat_template = ChatPromptTemplate.from_messages(
                [
                    ('system', """
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

            """),
                    ('system', '{agent_scratchpad}')
                ]
            )
            '''
            
            # agent = create_tool_calling_agent(self.client, [datahub_schema_search], prompt=chat_template)
            # self.agent_executor = AgentExecutor(agent=agent, tools=[datahub_schema_search], verbose=True)

            self.agent_executor  = initialize_agent(
                tools=[datahub_schema_search],
                llm=self.client,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True
            )


    async def generate(self, messages: list):
        """
        Gera uma resposta do modelo LLM usando a lista de mensagens.
        """
        return await self.client.ainvoke(messages)
    
    async def ask_with_tools(self, messages: str) -> str:
        await self.init_agent()
        return await self.agent_executor.ainvoke({"input": messages})

    async def resume_the_question_to_one_word(self, question: str) -> str:
        """
        Recebe uma pergunta e retorna apenas uma palavra como resposta.
        """
        prompt = [
            {"role": "system", "content": """
            Você precisa indentificar na pergunta o campo chave para uma procura em uma base.
            Você precisa retornar apenas uma palavra que será utilizada para procurar em uma base de dados.
            Analise a pergunta e responda com uma palavra chave
            """},
            {"role": "user", "content": question}
        ]
        resposta = await self.generate(prompt)
        # Extrai apenas a primeira palavra da resposta
        if hasattr(resposta, 'content'):
            text = resposta.content.strip()
        else:
            text = str(resposta).strip()
        return text.split()[0] if text else ""
    
    
    async def datahub_schema_search(self, question: str) -> str:
        """
        Usa GraphQL para buscar datasets e campos no DataHub com base no termo de busca fornecido.
        A busca percorre todas as páginas disponíveis.
        """
        resposta = await datahub_schema_search_logic(question)
        return resposta
        