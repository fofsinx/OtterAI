"""LLM provider package."""
from typing import Optional

from cori_ai.core.exceptions import ConfigurationError
from cori_ai.core.config import settings

from cori_ai.llm.base import BaseLLMProvider
from cori_ai.llm.openai_provider import OpenAIProvider
from cori_ai.llm.gemini_provider import GeminiProvider
from cori_ai.llm.anthropic_provider import AnthropicProvider
from cori_ai.llm.groq_provider import GroqProvider
from cori_ai.llm.mistral_provider import MistralProvider
from cori_ai.llm.ollama_provider import OllamaProvider

__all__ = [
    'BaseLLMProvider',
    'OpenAIProvider',
    'GeminiProvider',
    'AnthropicProvider',
    'GroqProvider',
    'MistralProvider',
    'OllamaProvider',
    'get_provider',
]

def get_provider(provider_name: Optional[str] = None, **kwargs) -> BaseLLMProvider:
    """Get an LLM provider instance.
    
    Args:
        provider_name: Name of the provider to use. If not provided, uses settings.provider.
        **kwargs: Additional arguments to pass to the provider constructor.
        
    Returns:
        LLM provider instance.
        
    Raises:
        ConfigurationError: If provider is not supported.
    """
    provider_name = provider_name or settings.provider
    
    providers = {
        'openai': OpenAIProvider,
        'gemini': GeminiProvider,
        'anthropic': AnthropicProvider,
        'groq': GroqProvider,
        'mistral': MistralProvider,
        'ollama': OllamaProvider,
    }
    
    if provider_name not in providers:
        raise ConfigurationError(
            f"Provider '{provider_name}' not supported. "
            f"Available providers: {', '.join(providers.keys())}"
        )
    
    return providers[provider_name](**kwargs) 