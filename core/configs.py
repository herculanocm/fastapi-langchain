from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    API_V1_STR: str = '/api/v1'
    DB_URL: str = 'postgresql+asyncpg://postgres:postgres@localhost:5432/teste'
    
    LLM_API_KEY: str 
    LLM_MODEL: str 
    LLM_TEMPERATURE: float 
    LLM_TOKEN_LIMIT: int
    LLM_ANSWER_LIMIT: int

    AGENT_MAX_INTERACTIONS: int = 100
    AGENT_MAX_EXECUTION_TIME: int = 180

    DATAHUB_JWT_KEY: str
    DATAHUB_URL: str = 'https://datacatalog.poligonocapital.io/api/graphql'

    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FILE: Optional[str] = None # Caminho para o arquivo de log, None para desabilitar
    
    WELLCOME_MESSAGE: str = """
        Olá! Você está conectado ao assistente de dados. Estou aqui para ajudar você a explorar e entender os dados disponíveis no DataHub da empresa.
        Você pode fazer perguntas sobre os datasets, suas colunas e como eles se relacionam. Além disso, posso ajudar a construir queries para buscar informações específicas.
        Para começar, basta me dizer o que você gostaria de saber ou explorar.
            """

    

    class Config:
        case_sensitive = True

settings = Settings()

def get_settings() -> Settings:
    return settings
