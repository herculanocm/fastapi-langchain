from langchain_openai import ChatOpenAI


class LLMService:
    def __init__(self, model: str, api_key: str, temperature: float = 0.7):
        self.model = model
        self.openai_api_key = api_key
        self.temperature = temperature
        self.client = ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            temperature=temperature
        )

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