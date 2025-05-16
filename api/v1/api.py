from fastapi import APIRouter
from api.v1.endpoints.llm import datahub

api_router = APIRouter()
api_router.include_router(datahub.router)



