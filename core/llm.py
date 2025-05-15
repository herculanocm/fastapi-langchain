from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
import aiohttp
import json

class LLMService:
    def __init__(self, model: str, api_key: str, temperature: float = 0.7, DATAHUB_JWT_KEY: str = None, DATAHUB_URL: str = None):
        self.model = model
        self.openai_api_key = api_key
        self.temperature = temperature
        self.client = ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            temperature=temperature
        )

        self.DATAHUB_JWT_KEY=DATAHUB_JWT_KEY
        self.DATAHUB_URL=DATAHUB_URL

    async def generate(self, messages: list):
        """
        Gera uma resposta do modelo LLM usando a lista de mensagens.
        """
        return await self.client.ainvoke(messages)

    async def resume_the_question_to_one_word(self, question: str) -> str:
        """
        Recebe uma pergunta e retorna apenas uma palavra como resposta.
        """
        prompt = [
            {"role": "system", "content": """
            Você precisa indentificar na pergunta o campo chave para uma procura em uma base.
            Você precisa retornar apenas uma palavra que será utilizada para procurar em uma base de dados.
            Analise a pergunta e responda com uma palavra chave
            """},
            {"role": "user", "content": question}
        ]
        resposta = await self.generate(prompt)
        # Extrai apenas a primeira palavra da resposta
        if hasattr(resposta, 'content'):
            text = resposta.content.strip()
        else:
            text = str(resposta).strip()
        return text.split()[0] if text else ""
    

    async def datahub_schema_search(self, search_term: str) -> str:
        """
        Usa GraphQL para buscar datasets e campos no DataHub com base no termo de busca fornecido.
        A busca percorre todas as páginas disponíveis.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.DATAHUB_JWT_KEY}"  # opcional
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
                            editableProperties {
                                description
                            }
                            schemaMetadata {
                                fields {
                                fieldPath
                                type
                                }
                            }
                            editableSchemaMetadata {
                                editableSchemaFieldInfo {
                                fieldPath
                                description
                                }
                            }
                            globalTags {
                                tags {
                                tag {
                                    name
                                }
                                }
                            }
                            }
                        }
                        }
                    }
                    }
                    """,
                    "variables": {
                        "query": search_term,
                        "start": start,
                        "count": count
                    }
                }

                async with session.post(self.DATAHUB_URL, json=query_payload, headers=headers) as response:
                    if response.status != 200:
                        return f"Erro ao consultar DataHub: status {response.status}"
                    data = await response.json()

                try:
                    if not data or "data" not in data or "search" not in data["data"]:
                        return f"Resposta inesperada da API na página {start}: {json.dumps(data, indent=2)}"

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
