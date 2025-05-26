import logging
import json


def _clean_string_formatting(text: str) -> str:
    """Remove quebras de linha, tabs e normaliza espaços em uma string."""
    if not isinstance(text, str):
        return text
    # Substitui quebras de linha e tabs por um espaço
    cleaned_text = text.replace('\n', ' ').replace('\t', ' ')
    # Remove espaços múltiplos e espaços no início/fim
    cleaned_text = ' '.join(cleaned_text.split())
    return cleaned_text

def _process_json_values_recursively(data):
    """
    Processa recursivamente uma estrutura de dados (lista ou dicionário)
    e aplica _clean_string_formatting a todos os valores de string.
    """
    if isinstance(data, list):
        return [_process_json_values_recursively(item) for item in data]
    elif isinstance(data, dict):
        return {key: _process_json_values_recursively(value) for key, value in data.items()}
    elif isinstance(data, str):
        return _clean_string_formatting(data)
    else:
        # Retorna outros tipos de dados (números, booleanos, None) como estão
        return data

def compress_json_array_to_string(json_array: list) -> str:
    """
    Recebe uma lista Python (representando um array JSON),
    remove formatações (quebras de linha, tabs, espaços duplos) de todos os campos de texto
    dentro dela e retorna sua representação em string JSON o mais comprimida possível.
    """
    if not isinstance(json_array, list):
        # Log ou erro mais específico pode ser útil aqui
        logging.warning("compress_json_array_to_string recebeu um tipo diferente de lista. Tentando processar de qualquer maneira.")
        # Ou levante um erro se uma lista for estritamente necessária:
        # raise TypeError("A entrada deve ser uma lista.")

    try:
        # Processa recursivamente a estrutura para limpar strings
        processed_array = _process_json_values_recursively(json_array)
        
        # Serializa para JSON sem espaços desnecessários
        # separators=(',', ':') remove todos os espaços após vírgulas e dois-pontos.
        compressed_string = json.dumps(processed_array, separators=(',', ':'))
        return compressed_string
    except TypeError as e:
        logging.error(f"Erro ao serializar o array JSON para string após limpeza: {e}")
        # Dependendo do comportamento desejado, pode-se retornar um valor padrão ou relançar
        # Retornando uma string JSON de array vazio como fallback seguro.
        return "[]" 
    except Exception as e:
        logging.error(f"Erro inesperado durante a compressão do JSON: {e}")
        return "[]"