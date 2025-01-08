"""Gemini provider implementation."""
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models.chat_models import BaseChatModel

from cori_ai.core.config import settings
from cori_ai.llm.base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    """Gemini provider using LangChain."""

    @property
    def llm(self) -> BaseChatModel:
        """Get the LangChain chat model instance.
        
        Returns:
            LangChain ChatGoogleGenerativeAI instance.
        """
        if not self._llm:
            self._llm = ChatGoogleGenerativeAI(
                api_key=self.api_key or settings.google_api_key,
                model=self.model,
                temperature=0.7,
                streaming=True,
                convert_system_message_to_human=True,
                max_retries=settings.max_retries,
            )
        return self._llm

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using Gemini's tokenizer.
        
        Args:
            text: Text to count tokens for.
            
        Returns:
            Number of tokens.
        """
        return self.llm.count_tokens(text)

    def get_token_limit(self) -> int:
        """Get the token limit for the current model.
        
        Returns:
            Maximum number of tokens supported by the model.
        """
        limits = {
            "gemini-1.5-flash": 128000,
            "gemini-1.5-pro": 32000,
            "gemini-pro": 32000,
        }
        return limits.get(self.model, 32000)  # Default to 32k if model not found
