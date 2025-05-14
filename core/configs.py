from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V1_STR: str = '/api/v1'
    DB_URL: str = 'postgresql+asyncpg://postgres:postgres@localhost:5432/teste'

    class Config:
        case_sensitive = True

settings = Settings()
def get_settings() -> Settings:
    return settings