from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from core.services.connection_manager_service import ConnectionManagerService
from core.deps import get_connection_manager
from core.services.thread_service import ThreadService
from core.deps import get_session, get_async_agent_service
from sqlalchemy.ext.asyncio import AsyncSession
from core.services.message_service import MessageService
import uuid # Para validar o formato do thread_id se for UUID
from core.configs import settings
import logging
from core.services.aync_agent_service import AsyncAgentService



router = APIRouter(
    prefix="/ws",
    tags=["WebSocket Chat"],
)

@router.websocket("/chat/{thread_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    thread_id: str,
    manager: ConnectionManagerService = Depends(get_connection_manager),
    session: AsyncSession = Depends(get_session),
    async_agent_service: AsyncAgentService = Depends(get_async_agent_service),
):
    """
    Endpoint WebSocket para chat dentro de uma thread específica.
    O `thread_id` é o identificador único do negócio que agrupa as mensagens.
    """
    client_host = websocket.client.host
    client_port = websocket.client.port

    # Opcional: Validar o formato do thread_id (ex: se for UUID)
    try:
        uuid.UUID(thread_id) # Tenta converter para UUID, se falhar, é inválido
    except ValueError:
        logging.warning(f"Invalid thread_id format: {thread_id}. Closing connection for {client_host}:{client_port}.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION) # Código para violação de política
        return

    thread_exists = await ThreadService.get_by_id(session=session, id=uuid.UUID(thread_id))
    if not thread_exists:
        logging.warning(f"Thread '{thread_id}' not found. Closing connection for {client_host}:{client_port}.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, thread_id)
    try:
        
        # Notificar outros na thread que um novo usuário entrou (opcional)
        await manager.broadcast_to_thread(role="server", conteudo= f"Usuário {client_host}:{client_port} entrou na thread.", thread_id=thread_id, sender=websocket)

        primeira_msg_thread = await MessageService.first_msg_thread(session=session, thread_id=thread_id)
        if primeira_msg_thread:
            await manager.send_personal_message(role="server", conteudo=settings.WELLCOME_MESSAGE.strip(), websocket=websocket)

        while True:

            raw_data = await websocket.receive_text()
            # Removendo double quotes do receive_text 
                  
            # Remove aspas duplas do início e do fim, se presentes
            msg_user = raw_data.strip('"') 

            logging.info(f"Mensagem recebida de {client_host}:{client_port} na thread '{thread_id}': {msg_user}")
            user_message = await MessageService.create_message_by_thread_id(session=session, thread_id=thread_id, role="user", content=msg_user.strip())
            await manager.send_personal_message(role="user", conteudo=user_message, websocket=websocket)

            history_message_model = await MessageService.list_by_thread_id_without_message_id(session=session, thread_id=thread_id, message_id=user_message.id)
            lls_history_messages = MessageService.to_dict_list(history_message_model)

            try:
                resposta = await async_agent_service.run(msg_user.strip(), lls_history_messages)
                # Valide se 'resposta' e 'resposta["output"]' existem e são o esperado
                if resposta is None or 'error' in resposta:
                    # Adicionando log de erro para formato de resposta inesperado do LLM
                    logging.error(f"Resposta do LLM em formato inesperado: {resposta}")
                    raise ValueError("Resposta do LLM em formato inesperado.")
                
                agent_message = await MessageService.create_message_by_thread_id(session=session, thread_id=thread_id, role="assistant", content=resposta)


                # Enviando mensaguem para o usuário da thread e do websocket
                await manager.send_personal_message(role="assistant", conteudo=agent_message, websocket=websocket) # Envia apenas para o usuário conectado


            except ValueError as ve: # Captura específica para o ValueError que criamos
                logging.error(f"Erro de valor ao processar resposta do LLM: {ve}")
                await manager.send_personal_message(role="server", conteudo= "Desculpe, ocorreu um erro ao processar a resposta do assistente. Por favor, tente novamente.", websocket=websocket)
                continue

            except Exception as llm_error:
                logging.error(f"Erro ao interagir com LLM ou processar sua resposta: {llm_error}", exc_info=True)
                await manager.send_personal_message(role="server", conteudo= f"Desculpe, ocorreu um erro ao tentar obter uma resposta do assistente. Por favor, tente novamente. (Erro: {str(llm_error)[:100]})", websocket=websocket)
                continue # Permite que o usuário envie outra mensagem
    
    except WebSocketDisconnect:
        logging.info(f"Client {client_host}:{client_port} desconectou da thread '{thread_id}'.")
        # Notificar outros na thread que o usuário saiu (opcional)
        await manager.broadcast_to_thread(role="server", conteudo=f"Usuário {client_host}:{client_port} saiu da thread.", thread_id=thread_id, sender=websocket)
    except Exception as e:
        logging.error(f"Erro inesperado com o client {client_host}:{client_port} na thread '{thread_id}': {e}", exc_info=True)
        # Tentar enviar uma mensagem de erro antes de fechar, se a conexão ainda permitir
        try:
            await websocket.send_text(f"Ocorreu um erro: {str(e)}. Desconectando.")
        except Exception:
            pass # Ignora se não conseguir enviar a mensagem de erro
    finally:
        # Garante que a desconexão seja registrada no manager
        manager.disconnect(websocket, thread_id)
        logging.info(f"Conexão limpa para {client_host}:{client_port} da thread '{thread_id}'.")




@router.post("/chat/{thread_id}/close_all", status_code=status.HTTP_204_NO_CONTENT)
async def close_all_thread_connections_endpoint(
    thread_id: str,
    manager: ConnectionManagerService = Depends(get_connection_manager)
):
    await manager.close_all_connections_for_thread(thread_id)
    return