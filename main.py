from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.configs import settings
from api.v1.api import api_router
#from core.logging_config import ensure_logging_configured

#ensure_logging_configured()

app = FastAPI(
    title="LLM API",
    description="API de LLM",
    version="1.0.0"
)

# Configurações de CORS
origins = [
    "http://localhost",
    "http://localhost:4200",
  ]  # Exemplo para Angular

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True
    )

