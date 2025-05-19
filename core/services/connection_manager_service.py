from fastapi import WebSocket
from collections import defaultdict
from typing import Dict, List
from schemas.message_ws import MessageWS
import logging

class ConnectionManagerService:
    def __init__(self):
        # Armazena conexões ativas, agrupadas por thread_id
        # Ex: {"thread_id_1": [websocket1, websocket2], "thread_id_2": [websocket3]}
        self.active_connections: Dict[str, List[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, thread_id: str):
        """Registra uma nova conexão WebSocket para uma thread específica."""
        await websocket.accept()
        self.active_connections[thread_id].append(websocket)
        logging.info(f"WebSocket {websocket.client.host}:{websocket.client.port} connected to thread '{thread_id}'.")

    def disconnect(self, websocket: WebSocket, thread_id: str):
        """Remove uma conexão WebSocket de uma thread específica."""
        if thread_id in self.active_connections:
            try:
                self.active_connections[thread_id].remove(websocket)
                logging.info(f"WebSocket {websocket.client.host}:{websocket.client.port} disconnected from thread '{thread_id}'.")
                # Se não houver mais conexões na thread, remove a entrada do dicionário para economizar memória
                if not self.active_connections[thread_id]:
                    del self.active_connections[thread_id]
                    logging.info(f"Thread '{thread_id}' is now empty and removed from active connections.")
            except ValueError:
                # Ocorre se o websocket já foi removido ou não estava na lista
                logging.warning(f"WebSocket {websocket.client.host}:{websocket.client.port} not found in thread '{thread_id}' for disconnection.")
                pass

    async def send_personal_message(self, role: str, conteudo: str, websocket: WebSocket):
        """Envia uma mensagem para um WebSocket específico."""
        try:
            message = MessageWS(role=role, content=conteudo)
            await websocket.send_json(message.model_dump())
        except Exception as e:
            # Lidar com o caso de o websocket não estar mais ativo
            logging.error(f"Error sending personal message to {websocket.client.host}:{websocket.client.port}: {e}")
            # Considerar remover a conexão se estiver quebrada, embora disconnect deva cuidar disso

    async def broadcast_to_thread(self, role: str, conteudo: str, thread_id: str, sender: WebSocket = None):
        """Envia uma mensagem para todos os WebSockets conectados a uma thread específica, opcionalmente excluindo o remetente."""
        if thread_id in self.active_connections:
            # Iterar sobre uma cópia da lista para permitir modificações (desconexões) durante a iteração
            connections_in_thread = list(self.active_connections[thread_id])
            logging.info(f"Broadcasting to thread '{thread_id}': {len(connections_in_thread)} connections.")
            for connection in connections_in_thread:
                if connection != sender: # Não envia de volta para o remetente, se especificado
                    try:
                        message = MessageWS(role=role, content=conteudo)
                        await connection.send_json(message.model_dump())
                    except Exception as e:
                        # Se a conexão estiver quebrada, desconecte-a
                        logging.error(f"Error broadcasting to {connection.client.host}:{connection.client.port} in thread '{thread_id}': {e}. Disconnecting.")
                        self.disconnect(connection, thread_id)
        else:
            logging.info(f"No active connections in thread '{thread_id}' to broadcast to.")

    async def close_all_connections_for_thread(self, thread_id: str):
        """Fecha todas as conexões para uma thread específica."""
        if thread_id in self.active_connections:
            connections_to_close = list(self.active_connections[thread_id])
            logging.info(f"Closing all {len(connections_to_close)} connections for thread '{thread_id}'.")
            for websocket in connections_to_close:
                try:
                    await websocket.close(code=1000) # Código 1000 indica fechamento normal
                except Exception:
                    pass # Ignora erros ao tentar fechar, pois estamos limpando
                self.disconnect(websocket, thread_id) # Garante a remoção da lista
            if thread_id in self.active_connections: # Verifica novamente, pois disconnect pode ter removido
                 del self.active_connections[thread_id]

    async def close_all_connections(self):
        """Fecha todas as conexões ativas em todas as threads."""
        all_thread_ids = list(self.active_connections.keys())
        logging.info(f"Closing all connections across {len(all_thread_ids)} threads.")
        for thread_id in all_thread_ids:
            await self.close_all_connections_for_thread(thread_id)

    async def close(self):
        """Fecha todas as conexões ativas e limpa o gerenciador."""
        await self.close_all_connections()
        logging.info("Connection manager closed and all connections cleaned up.")