
def count_words(messages):
    if messages is None or len(messages) == 0:
        return 0
    return sum(len(str(msg.get("content", "")).split()) for msg in messages)


def truncate_messages_llama(system_prompt: dict, historico: list, user_question: dict, assistant_message: dict, modelo: str, token_limit: int, reserve_tokens_response):
    
    qtd_tokens_assistant_message = 0
    if assistant_message is not None:
        qtd_tokens_assistant_message = count_words([assistant_message])

    question_tokens = (
        count_words([system_prompt]) + 
        count_words([user_question]) + 
        qtd_tokens_assistant_message +
        reserve_tokens_response
        )
    
    total_tokens = count_words(historico) + question_tokens
    
    if total_tokens <= token_limit:
        return historico

    
    max_history_tokens = token_limit - question_tokens

    if max_history_tokens <= 0:
        return []
    # reduz o histórico para o número máximo de tokens permitido
    truncated_history = []
    for message in reversed(historico):
        message_tokens = count_words([message])
        history_tokens = count_words(truncated_history)
        if history_tokens + message_tokens <= max_history_tokens:
            truncated_history.append(message)
        else:
            break
    # inverte a lista de mensagens truncadas para manter a ordem original
    return truncated_history.reverse()