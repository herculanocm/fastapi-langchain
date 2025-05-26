import tiktoken

def count_tokens_openai(messages: list, model: str):
    # or none
    if messages is None or len(messages) == 0:
        return 0
    
    enc = tiktoken.encoding_for_model(model)
    num_tokens = 0
    for message in messages:
        # Cada mensagem tem role e content
        num_tokens += 4  # tokens de formatação
        for key, value in message.items():
            num_tokens += len(enc.encode(str(value)))
    num_tokens += 2  # priming
    return num_tokens

def truncate_messages_openai_for_subject(system_prompt: dict, historico: list, user_question: dict, token_limit: int, reserve_tokens_response: int, model: str):
    # Se o histórico estiver vazio, não há necessidade de truncar
    if not historico:
        return historico

    system_prompt_tokens = count_tokens_openai([system_prompt], model)
    user_question_tokens = count_tokens_openai([user_question], model)
    history_tokens = count_tokens_openai(historico, model)
    total_tokens = system_prompt_tokens + user_question_tokens + history_tokens + reserve_tokens_response
    if total_tokens <= token_limit:
        return historico
    
    # Se o total de tokens exceder o limite, reduz o histórico
    max_history_tokens = token_limit - system_prompt_tokens - user_question_tokens - reserve_tokens_response
    if max_history_tokens <= 0:
        return []
    
    # reduz o histórico para o número máximo de tokens permitido
    truncated_history = []
    # Para o metodo subject não é necessário inverter a ordem
    for message in historico:
        message_tokens = count_tokens_openai([message], model)
        history_tokens = count_tokens_openai(truncated_history, model)
        if history_tokens + message_tokens <= max_history_tokens:
            truncated_history.append(message)
        else:
            break
    # não inverte a lista de mensagens truncadas para manter a ordem original
    return truncated_history

def truncate_messages_openai_v2(system_prompt: dict, historico: list, user_question: dict, assistant_message: dict, modelo: str, token_limit: int, reserve_tokens_response):
    """
    Trunca o histórico de mensagens para se adequar ao limite de tokens do modelo OpenAI.
    """
    # Se o histórico estiver vazio, não há necessidade de truncar
    if not historico:
        return historico

    system_prompt_tokens = count_tokens_openai([system_prompt], modelo)
    user_question_tokens = count_tokens_openai([user_question], modelo)
    
    assistant_message_tokens = 0
    if assistant_message is not None:
        assistant_message_tokens = count_tokens_openai([assistant_message], modelo)

    history_tokens = count_tokens_openai(historico, modelo)
    total_tokens = system_prompt_tokens  + history_tokens + user_question_tokens + assistant_message_tokens + reserve_tokens_response

    if total_tokens <= token_limit:
        return historico
    
    # Se o total de tokens exceder o limite, reduz o histórico
    max_history_tokens = token_limit - system_prompt_tokens - user_question_tokens - assistant_message_tokens - reserve_tokens_response
    if max_history_tokens <= 0:
        return []
    
    # reduz o histórico para o número máximo de tokens permitido
    truncated_history = []
    for message in reversed(historico):
        message_tokens = count_tokens_openai([message], modelo)
        history_tokens = count_tokens_openai(truncated_history, modelo)
        if history_tokens + message_tokens <= max_history_tokens:
            truncated_history.append(message)
        else:
            break
    # inverte a lista de mensagens truncadas para manter a ordem original
    truncated_history.reverse()
    return truncated_history