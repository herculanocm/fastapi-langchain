from fastapi import APIRouter
from api.v1.endpoints.llm import datahub
from api.v1.websockets import chat_ws
from api.v1.endpoints import thread_message_resource, message_resource

api_router = APIRouter()
api_router.include_router(thread_message_resource.router)
api_router.include_router(message_resource.router)
api_router.include_router(datahub.router)
api_router.include_router(chat_ws.router)



