from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = '/api/v1'
    DB_URL: str = 'postgresql+asyncpg://postgres:postgres@localhost:5432/teste'
    
    LLM_API_KEY: str 
    LLM_MODEL: str 
    LLM_TEMPERATURE: float 

    DATAHUB_JWT_KEY: str
    DATAHUB_URL: str = 'https://datacatalog.poligonocapital.io/api/graphql'

    START_MESSAGE: str = """
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

            Responda sempre em português.
            """
    

    class Config:
        case_sensitive = True

settings = Settings()

def get_settings() -> Settings:
    return settings
