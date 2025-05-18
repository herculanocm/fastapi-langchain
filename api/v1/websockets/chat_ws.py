from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from core.services.connection_manager_service import ConnectionManagerService
from core.deps import get_connection_manager

router = APIRouter(
    prefix="/ws",
)


@router.websocket("/chat/{email}/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, email: str, thread_id: str, manager: ConnectionManagerService = Depends(get_connection_manager)):
    await manager.connect(websocket)
    try:
        await websocket.send_text(f"Connected to chat thread {thread_id} as {email}")
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"Error: {e}")