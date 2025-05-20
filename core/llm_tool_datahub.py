import aiohttp
import json
from langchain_core.tools import tool
from core.configs import settings

@tool
async def datahub_schema_search(question: str) -> str:
    """
    Usa GraphQL para buscar datasets e campos no DataHub com base no termo de busca fornecido.
    ### Como usar a ferramenta:

    - Utilize **termos descritivos** relacionados a tabelas, colunas, TAGs, dados ou domínios de negócio.
    - O campo de busca aceita **termos simples**, **frases**, ou **buscas compostas** com operadores como AND, OR, NOT e wildcards (como `clientes*`).
    - Exemplos de termos válidos:
    - `"clientes"`
    - `"vendas AND 2023"`
    - `"transacoes NOT canceladas"`
    - `"\"usuarios ativos\""`
    - `"clientes*"`
    """
    return await datahub_schema_search_logic_list(question)


def structure_results_for_json(dataset: dict, fields: list, field_descriptions: list, tags: list) -> dict:
    name = dataset.get("name", "N/A")
    editable = dataset.get("editableProperties") or {}
    desc = editable.get("description", "Sem descrição")
    
    
    tag_names = [tag.get("tag", {}).get("name") for tag in tags if tag.get("tag") and tag["tag"].get("name")]

    structured_fields = []
    for field in fields:
        path = field.get("fieldPath", "-")
        ftype = field.get("type", "unknown")
        description = next(
            (fd.get("description", "—") for fd in field_descriptions if fd.get("fieldPath") == path),
            "—"
        )
        structured_fields.append({
            "name": path,
            "type": ftype,
            "description": description
        })

    return {
        "name": name,
        "description": desc,
        "tags": tag_names,
        "fields": structured_fields
    }

async def datahub_schema_search_logic_list(question: str) -> list:
    """
    Usa GraphQL para buscar datasets e campos no DataHub com base no termo de busca fornecido.
    Retorna uma lista de dicionários estruturados.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.DATAHUB_JWT_KEY}"
    }

    all_results = []
    start = 0
    count = 50
    total = None

    async with aiohttp.ClientSession() as session:
        while total is None or start < total:
            query_payload = {
                "query": """
                query getTablesAndColumns($query: String!, $start: Int!, $count: Int!) {
                  search(input: {type: DATASET, query: $query, start: $start, count: $count}) {
                    start
                    count
                    total
                    searchResults {
                      entity {
                        ... on Dataset {
                          name
                          editableProperties { description }
                          schemaMetadata { fields { fieldPath type } }
                          editableSchemaMetadata { editableSchemaFieldInfo { fieldPath description } }
                          globalTags { tags { tag { name } } }
                        }
                      }
                    }
                  }
                }
                """,
                "variables": {
                    "query": question,
                    "start": start,
                    "count": count
                }
            }

            async with session.post(settings.DATAHUB_URL, json=query_payload, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"Erro ao consultar DataHub: status {response.status}")
                data = await response.json()

            try:
                if not data or "data" not in data or "search" not in data["data"]:
                    raise ValueError(f"Resposta inesperada da API na página {start}: {json.dumps(data, indent=2)}")

                if "errors" in data:
                    raise ValueError(f"Erro do GraphQL: {json.dumps(data['errors'], indent=2)}")

                search_data = data["data"]["search"]
                total = search_data.get("total", 0)
                search_results = search_data.get("searchResults", [])

                for result in search_results:
                    dataset = result.get("entity", {})
                    schemaMetadata = dataset.get("schemaMetadata") or {}
                    fields = schemaMetadata.get("fields", [])

                    editableSchemaMetadata = dataset.get("editableSchemaMetadata") or {}
                    field_descriptions = editableSchemaMetadata.get("editableSchemaFieldInfo", [])
                    globalTags = dataset.get("globalTags") or {}
                    tags = globalTags.get("tags", [])

                    structured = structure_results_for_json(dataset, fields, field_descriptions, tags)
                    all_results.append(structured)

                start += count

            except Exception as e:
                raise RuntimeError(f"Erro ao processar resposta na página {start}: {str(e)}")

    return all_results



async def datahub_schema_search_logic(question: str) -> str:
    """
    Usa GraphQL para buscar datasets e campos no DataHub com base no termo de busca fornecido.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.DATAHUB_JWT_KEY}"
    }

    all_results = []
    start = 0
    count = 50
    total = None

    async with aiohttp.ClientSession() as session:
        while total is None or start < total:
            query_payload = {
                "query": """
                query getTablesAndColumns($query: String!, $start: Int!, $count: Int!) {
                  search(input: {type: DATASET, query: $query, start: $start, count: $count}) {
                    start
                    count
                    total
                    searchResults {
                      entity {
                        ... on Dataset {
                          name
                          editableProperties { description }
                          schemaMetadata { fields { fieldPath type } }
                          editableSchemaMetadata { editableSchemaFieldInfo { fieldPath description } }
                          globalTags { tags { tag { name } } }
                        }
                      }
                    }
                  }
                }
                """,
                "variables": {
                    "query": question,
                    "start": start,
                    "count": count
                }
            }

            async with session.post(settings.DATAHUB_URL, json=query_payload, headers=headers) as response:
                if response.status != 200:
                    return f"Erro ao consultar DataHub: status {response.status}"
                data = await response.json()

            try:
                if not data or "data" not in data or "search" not in data["data"]:
                    return f"Resposta inesperada da API na página {start}: {json.dumps(data, indent=2)}"
                
                if "errors" in data:
                    return f"Erro do GraphQL: {json.dumps(data['errors'], indent=2)}"

                search_data = data["data"]["search"]
                total = search_data.get("total", 0)
                search_results = search_data.get("searchResults", [])

                for result in search_results:
                    dataset = result.get("entity", {})
                    name = dataset.get("name", "N/A")
                    editable = dataset.get("editableProperties") or {}
                    desc = editable.get("description", "Sem descrição")
                    fields = dataset.get("schemaMetadata", {}).get("fields", [])
                    editableSchemaMetadata = dataset.get("editableSchemaMetadata") or {}
                    field_descriptions = editableSchemaMetadata.get("editableSchemaFieldInfo", [])
                    globalTags = dataset.get("globalTags") or {}
                    tags = globalTags.get("tags", [])

                    tag_names = [tag.get("tag", {}).get("name") for tag in tags if tag.get("tag")]
                    tag_line = f" Tags: {', '.join(tag_names)}" if tag_names else ""

                    all_results.append(f"\n Dataset: {name}\n Descrição: {desc}\n{tag_line}")
                    for field in fields:
                        path = field.get("fieldPath", "-")
                        ftype = field.get("type", "unknown")
                        description = next(
                            (fd.get("description", "—") for fd in field_descriptions if fd.get("fieldPath") == path),
                            "—"
                        )
                        all_results.append(f"  ▸ {path} ({ftype}): {description}")

                start += count

            except Exception as e:
                return f"Erro ao processar resposta na página {start}: {str(e)}"

    return "\n".join(all_results) if all_results else "Nenhum dataset encontrado."