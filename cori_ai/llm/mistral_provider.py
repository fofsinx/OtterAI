"""Mistral provider implementation."""
from typing import Optional

from langchain_mistralai.chat_models import ChatMistralAI
from langchain_core.language_models.chat_models import BaseChatModel

from cori_ai.core.config import settings
from cori_ai.llm.base import BaseLLMProvider


class MistralProvider(BaseLLMProvider):
    """Mistral provider using LangChain."""

    @property
    def llm(self) -> BaseChatModel:
        """Get the LangChain chat model instance.
        
        Returns:
            LangChain ChatMistralAI instance.
        """
        if not self._llm:
            self._llm = ChatMistralAI(
                api_key=self.api_key or settings.mistral_api_key,
                model=self.model,
                temperature=0.7,
                streaming=True,
                max_retries=settings.max_retries,
            )
        return self._llm
