"""Groq provider implementation."""
from typing import Optional

from langchain_groq import ChatGroq
from langchain_core.language_models.chat_models import BaseChatModel

from cori_ai.core.config import settings
from cori_ai.llm.base import BaseLLMProvider

class GroqProvider(BaseLLMProvider):
    """Groq provider using LangChain."""

    @property
    def llm(self) -> BaseChatModel:
        """Get the LangChain chat model instance.
        
        Returns:
            LangChain ChatGroq instance.
        """
        if not self._llm:
            self._llm = ChatGroq(
                api_key=self.api_key or settings.groq_api_key,
                model=self.model,
                temperature=0.7,
                streaming=True,
                max_retries=settings.max_retries,
            )
        return self._llm

    def count_tokens(self, text: str) -> int:
        """Count tokens in text.
        
        Args:
            text: Text to count tokens for.
            
        Returns:
            Number of tokens.
        """
        # Groq doesn't provide a token counter, use approximation
        return len(text.split()) * 1.3

    def get_token_limit(self) -> int:
        """Get the token limit for the current model.
        
        Returns:
            Maximum number of tokens supported by the model.
        """
        limits = {
            "mixtral-8x7b-32768": 32768,
            "llama2-70b-4096": 4096,
            "gemma-7b-it": 8192,
        }
        return limits.get(self.model, 4096)  # Default to 4096 if model not found 