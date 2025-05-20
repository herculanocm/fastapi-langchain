from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    API_V1_STR: str = '/api/v1'
    DB_URL: str = 'postgresql+asyncpg://postgres:postgres@localhost:5432/teste'
    
    LLM_API_KEY: str 
    LLM_MODEL: str 
    LLM_TEMPERATURE: float 

    DATAHUB_JWT_KEY: str
    DATAHUB_URL: str = 'https://datacatalog.poligonocapital.io/api/graphql'

    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FILE: Optional[str] = None # Caminho para o arquivo de log, None para desabilitar


    START_MESSAGE: str = """
            Você tem acesso a uma ferramenta chamada `datahub_schema_search(question: str)` que constrói uma query GraphQL para buscar datasets e suas colunas dentro do DataHub da empresa.

            ### Como usar a ferramenta:

            - Utilize **termos descritivos** relacionados a tabelas, colunas, TAGs, dados ou domínios de negócio.
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

            ### Retorno de código:
            Caso o usuário solicite um retorno em SQL, você deve retornar uma query SQL válida para o banco de dados AWS Redshift.
            Não existe ferramenta para gerar o SQL, então atraves do retorno da ferramenta `datahub_schema_search(question: str)` você deve gerar o SQL utilizando seus conhecimentos de SQL.
            A tabela no data catalog sempre vem acompanhada do database.schema.tabela, ao formar o SQL, você deve retirar o database e deixar apenas o schema.tabela.
            
            Exemplo:
            ```sql
            SELECT * FROM captalys_analytics.d_calendario
            ```

            Responda sempre em português.

            ### IMPORTANTE: FORMATO DE RESPOSTA DO AGENTE
            Sempre siga o formato abaixo em cada passo do raciocínio:
            Thought: [explique seu pensamento]
            Action: [nome_da_ferramenta]
            Action Input: [entrada para a ferramenta]
            Observation: [resultado da ferramenta]
            ... (repita Thought/Action/Action Input/Observation quantas vezes precisar) ...
            Final Answer: [resposta final ao usuário]

            Se a resposta não requer o uso de ferramenta, vá diretamente para:
            Final Answer: [sua resposta final]
            Nunca invente uma Action que não existe. Só use Action se for realmente usar uma ferramenta registrada.
            """
    
    WELLCOME_MESSAGE: str = """
Olá! Você está conectado ao assistente de dados. Estou aqui para ajudar você a explorar e entender os dados disponíveis no DataHub da empresa.
Você pode fazer perguntas sobre os datasets, suas colunas e como eles se relacionam. Além disso, posso ajudar a construir queries para buscar informações específicas.
Para começar, basta me dizer o que você gostaria de saber ou explorar.
            """
    LLM_MAX_TOKENS: int = 2000
    AGENT_MAX_INTERACTIONS: int = 100
    AGENT_MAX_EXECUTION_TIME: int = 180
    

    class Config:
        case_sensitive = True

settings = Settings()

def get_settings() -> Settings:
    return settings
