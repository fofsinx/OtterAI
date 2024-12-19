"""Anthropic provider implementation."""
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel

from otterai.core.config import settings
from otterai.llm.base import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    """Anthropic provider using LangChain."""

    @property
    def llm(self) -> BaseChatModel:
        """Get the LangChain chat model instance.
        
        Returns:
            LangChain ChatAnthropic instance.
        """
        if not self._llm:
            self._llm = ChatAnthropic(
                api_key=self.api_key or settings.anthropic_api_key,
                model=self.model,
                temperature=0.7,
                streaming=True,
                max_retries=settings.max_retries,
                anthropic_api_url="https://api.anthropic.com/v1",
            )
        return self._llm

    def count_tokens(self, text: str) -> float:
        """Count tokens in text using Anthropic tokenizer.
        
        Args:
            text: Text to count tokens for.
            
        Returns:
            Number of tokens.
        """
        # Anthropic doesn't provide a token counter, use approximation
        return len(text.split()) * 1.3

    def get_token_limit(self) -> int:
        """Get the token limit for the current model.
        
        Returns:
            Maximum number of tokens supported by the model.
        """
        limits = {
            "claude-3-opus": 200000,
            "claude-3-sonnet": 200000,
            "claude-3-haiku": 200000,
            "claude-2.1": 200000,
            "claude-2.0": 100000,
            "claude-instant-1.2": 100000,
        }
        return limits.get(self.model, 100000)  # Default to 100k if model not found
