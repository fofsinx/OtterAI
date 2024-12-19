"""OpenAI provider implementation."""
from typing import Optional
import httpx

from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel

from otterai.core.config import settings
from otterai.llm.base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider using LangChain."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        super().__init__(api_key, model)

    @property
    def llm(self) -> BaseChatModel:
        """Get the LangChain chat model instance.
        
        Returns:
            LangChain ChatOpenAI instance.
        """
        if not self._llm:
            self._llm = ChatOpenAI(
                api_key=self.api_key or settings.openai_api_key,
                model=self.model,
                base_url=settings.openai_base_url,
                streaming=True,
                temperature=0.7,
                request_timeout=60,
                async_client=httpx.AsyncClient(),
                max_retries=settings.max_retries,
            )
        return self._llm

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken.
        
        Args:
            text: Text to count tokens for.
            
        Returns:
            Number of tokens.
        """
        return len(self._encoding.encode(text))

    def get_token_limit(self) -> int:
        """Get the token limit for the current model.
        
        Returns:
            Maximum number of tokens supported by the model.
        """
        limits = {
            "gpt-4-turbo-preview": 128000,
            "gpt-4": 8192,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384,
        }
        return limits.get(self.model, 4096)  # Default to 4096 if model not found
