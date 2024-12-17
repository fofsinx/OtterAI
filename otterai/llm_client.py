import os
import httpx
from langchain_openai import ChatOpenAI

class LLMClient:
    _instance = None

    def __new__(cls) -> 'LLMClient':
        if cls._instance is None:
            cls._instance = super(LLMClient, cls).__new__(cls)
            cls._instance.client = ChatOpenAI(
                model_name=os.getenv('INPUT_MODEL', 'gpt-4-turbo-preview'),
                http_async_client=httpx.AsyncClient(timeout=60.0),
                api_key=os.getenv('INPUT_OPENAI_API_KEY'),
                base_url=os.getenv('INPUT_OPENAI_BASE_URL', 'https://api.openai.com/v1'),
                temperature=0.1
            )
        return cls._instance

    def get_client(self) -> ChatOpenAI:
        return self._instance.client 