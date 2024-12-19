"""Ollama provider implementation using LangChain."""
from typing import Optional

from langchain_community.chat_models import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel

from otterai.core.config import settings
from otterai.llm.base import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    """Ollama provider using LangChain."""

    @property
    def llm(self) -> BaseChatModel:
        """Get the LangChain chat model instance.
        
        Returns:
            LangChain ChatOllama instance.
        """
        if not self._llm:
            self._llm = ChatOllama(
                model=self.model,
                temperature=0.7,
                streaming=True,
                base_url=settings.ollama_base_url,
                callback_manager=settings.callback_manager,
                max_retries=settings.max_retries,
                request_timeout=60,
                # Additional Ollama-specific parameters
                mirostat=1,  # Enable Mirostat sampling for better output consistency
                mirostat_eta=0.1,  # Learning rate for Mirostat
                mirostat_tau=5.0,  # Target entropy for Mirostat
                num_ctx=4096,  # Context window size
                num_gpu=1,  # Number of GPUs to use
                num_thread=8,  # Number of CPU threads to use
                repeat_last_n=64,  # Last n tokens to consider for repetition
                repeat_penalty=1.1,  # Penalty for repetition
                seed=-1,  # Random seed (-1 for random)
                stop=["</s>", "Human:", "Assistant:"],  # Stop sequences
                tfs_z=1.0,  # Tail free sampling parameter
                top_k=40,  # Top-k sampling parameter
                top_p=0.9,  # Top-p sampling parameter
            )
        return self._llm

    def count_tokens(self, text: str) -> int:
        """Count tokens in text.
        
        Args:
            text: Text to count tokens for.
            
        Returns:
            Number of tokens.
        """
        # Ollama doesn't provide a token counter, use approximation
        return len(text.split()) * 1.3

    def get_token_limit(self) -> int:
        """Get the token limit for the current model.
        
        Returns:
            Maximum number of tokens supported by the model.
        """
        limits = {
            "llama2": 4096,
            "codellama": 16384,
            "mistral": 8192,
            "mixtral": 32768,
            "gemma": 8192,
            "phi": 2048,
            "qwen": 32768,
            "neural-chat": 8192,
            "starling-lm": 8192,
            "stable-beluga": 4096,
            "vicuna": 2048,
            "zephyr": 16384,
        }
        # Try to match model name prefix
        for model_prefix, limit in limits.items():
            if self.model.startswith(model_prefix):
                return limit
        return 4096  # Default to 4096 if model not found 