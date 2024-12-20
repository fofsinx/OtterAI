import os
from typing import Optional
import httpx
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_core.language_models.chat_models import BaseChatModel
import logging

class LLMClient:
    _instance = None
    _client: Optional[BaseChatModel] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMClient, cls).__new__(cls)
        return cls._instance

    def _init_openai(self) -> BaseChatModel:
        """Initialize OpenAI client."""
        return ChatOpenAI(
            model_name=os.getenv('INPUT_MODEL', 'gpt-4o-mini'),
            api_key=os.getenv('INPUT_OPENAI_API_KEY'),
            http_async_client=httpx.AsyncClient(timeout=60.0),
            base_url=os.getenv('INPUT_OPENAI_BASE_URL', 'https://api.openai.com/v1'),
            temperature=0.1
        )

    def _init_gemini(self) -> BaseChatModel:
        """Initialize Google Gemini client."""
        return ChatGoogleGenerativeAI(
            model=os.getenv('INPUT_MODEL', 'gemini-1.5-flash'),
            api_key=os.getenv('INPUT_GOOGLE_API_KEY'),
            temperature=0.1
        )

    def _init_groq(self) -> BaseChatModel:
        """Initialize Groq client."""
        return ChatGroq(
            api_key=os.getenv('INPUT_GROQ_API_KEY'),
            model_name=os.getenv('INPUT_MODEL', 'mixtral-8x7b-32768'),
            temperature=0.1
        )

    def _init_mistral(self) -> BaseChatModel:
        """Initialize Mistral client."""
        return ChatMistralAI(
            api_key=os.getenv('INPUT_MISTRAL_API_KEY'),
            model_name=os.getenv('INPUT_MODEL', 'mistral-large-latest'),
            temperature=0.1
        )
        
    def _init_ollama(self) -> BaseChatModel:
        """Initialize Ollama client."""
        return ChatOllama(
            model=os.getenv('INPUT_MODEL', 'codellama:7b'),
            base_url=os.getenv('INPUT_OLLAMA_BASE_URL', 'http://localhost:11434'),
            api_key=os.getenv('INPUT_OLLAMA_API_KEY'),
            temperature=0.1
        )

    def get_client(self) -> BaseChatModel:
        """Get LLM client based on provider."""
        if self._client is not None:
            return self._client

        provider = os.getenv('INPUT_PROVIDER', 'openai').lower()
        try:
            if provider == 'openai':
                self._client = self._init_openai()
            elif provider == 'gemini':
                self._client = self._init_gemini()
            elif provider == 'groq':
                self._client = self._init_groq()
            elif provider == 'mistral':
                self._client = self._init_mistral()
            elif provider == 'ollama':
                self._client = self._init_ollama()
            else:
                logging.error(f"Unsupported provider: {provider}, falling back to OpenAI")
                self._client = self._init_openai()
        except Exception as e:
            logging.error(f"Error initializing {provider} client: {str(e)}")
            raise

        return self._client

    def reset_client(self):
        """Reset the LLM client."""
        self._client = None