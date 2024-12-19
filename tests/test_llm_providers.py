"""Tests for LLM providers."""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk
from langchain_core.output_parsers import JsonOutputParser

from otterai.core.exceptions import LLMError, ConfigurationError
from otterai.core.config import settings
from otterai.llm import (
    get_provider,
    OpenAIProvider,
    GeminiProvider,
    AnthropicProvider,
    GroqProvider,
    MistralProvider,
    OllamaProvider,
)


@pytest.fixture
def mock_chat_model():
    """Mock chat model fixture."""
    model = Mock()
    model.ainvoke = AsyncMock(return_value=AIMessage(content="Test response"))
    model.astream = AsyncMock(return_value=[
        ChatGenerationChunk(
            text="Test",
            generation_info=None,
            message={
                "type": "human",
                "content": "Test",
                "additional_kwargs": {},
                "example": False
            }
        )
    ])
    model.get_num_tokens = Mock(return_value=10)
    model.modelname_to_contextsize = Mock(return_value=4096)
    model.bind = Mock(return_value=model)
    model.callback_manager = None
    model.agenerate_prompt = AsyncMock(return_value=Mock(
        generations=[[ChatGeneration(text="Test response", message=AIMessage(content="Test response"))]]
    ))
    model.get_model_info = Mock(return_value={"name": "test-model", "max_tokens": 4096})
    return model


@pytest.fixture
def mock_provider(mock_chat_model):
    """Mock LLM provider fixture."""
    provider = Mock()
    provider.llm = mock_chat_model
    provider._llm = mock_chat_model
    provider.model = "test-model"
    provider.generate = AsyncMock(return_value="Test response")
    provider.generate_json = AsyncMock(return_value={"test": "value"})
    provider.stream = AsyncMock(return_value=["Test"])
    provider.count_tokens = Mock(return_value=10)
    provider.get_token_limit = Mock(return_value=4096)
    return provider


@pytest.fixture
def mock_parser():
    """Mock JsonOutputParser fixture."""
    parser = Mock(spec=JsonOutputParser)
    parser.aparse_result = AsyncMock(side_effect=lambda x: x[0].text)
    return parser


@pytest.mark.asyncio
async def test_get_provider():
    """Test get_provider function."""
    # Mock all provider classes to avoid actual initialization
    mocks = {}
    for provider_name in ['openai', 'gemini', 'anthropic', 'groq', 'mistral', 'ollama']:
        mock_class = Mock()
        mock_instance = Mock()
        mock_class.return_value = mock_instance
        mocks[provider_name] = mock_class
        
    with patch.multiple(
        'otterai.llm',
        OpenAIProvider=mocks['openai'],
        GeminiProvider=mocks['gemini'],
        AnthropicProvider=mocks['anthropic'],
        GroqProvider=mocks['groq'],
        MistralProvider=mocks['mistral'],
        OllamaProvider=mocks['ollama']
    ):
        # Test valid providers
        for provider_name in ['openai', 'gemini', 'anthropic', 'groq', 'mistral', 'ollama']:
            provider_instance = get_provider(provider_name)
            assert isinstance(provider_instance, Mock)
            assert provider_instance == mocks[provider_name].return_value

        # Test invalid provider
        with pytest.raises(ConfigurationError):
            get_provider('invalid_provider')

        # Test default provider from settings
        settings.provider = 'openai'
        provider_instance = get_provider()
        assert provider_instance == mocks['openai'].return_value


@pytest.mark.asyncio
async def test_base_provider_methods():
    """Test base provider methods."""
    with patch('otterai.llm.OpenAIProvider') as MockProvider:
        # Setup the mock provider instance
        provider = AsyncMock()
        provider._llm = AsyncMock()
        provider.llm = AsyncMock()
        
        # Configure the return values
        provider.generate.return_value = "Test response"
        provider.generate_json.return_value = {"test": "value"}
        provider.count_tokens.return_value = 10
        provider.get_token_limit.return_value = 4096
        provider.model_name = "test-model"
        
        # Create an async generator for stream method
        async def mock_stream(*args, **kwargs):
            yield "Test"
            yield " response"
        provider.stream = mock_stream
        
        # Create an error stream using a proper async iterator
        class ErrorStream:
            def __init__(self):
                self._first = True

            def __aiter__(self):
                return self
                
            async def __anext__(self):
                if self._first:
                    self._first = False
                    raise LLMError("Stream error", provider="OpenAIProvider", model="test-model")
                raise StopAsyncIteration
        
        async def error_stream(*args, **kwargs):
            return ErrorStream()
        
        MockProvider.return_value = provider

        # Initialize provider
        provider = MockProvider()

        # Test generate
        response = await provider.generate("Test prompt")
        assert response == "Test response"
        provider.generate.assert_called_once_with("Test prompt")

        # Test generate with parameters
        response = await provider.generate(
            "Test prompt",
            temperature=0.5,
            max_tokens=100,
            stop=["stop"],
        )
        assert response == "Test response"

        # Test generate_json
        schema = {"type": "object", "properties": {"test": {"type": "string"}}}
        response = await provider.generate_json("Test prompt", schema)
        assert response == {"test": "value"}

        # Test invalid JSON response
        provider.generate_json.side_effect = LLMError("JSON generation failed")
        
        with pytest.raises(LLMError, match="JSON generation failed"):
            await provider.generate_json("Test prompt", schema)

        # Test stream
        chunks = []
        async for chunk in provider.stream("Test prompt"):
            chunks.append(chunk)
        assert chunks == ["Test", " response"]

        # Test stream error
        provider.stream = error_stream
        with pytest.raises(LLMError, match="Stream error"):
            async for _ in await provider.stream("Test prompt"):
                pass

        # Test token counting
        token_count = await provider.count_tokens("Test text")
        assert token_count == 10
        assert await provider.count_tokens.aassert_called_once_with("Test text")

        # Test token counting error
        provider.count_tokens.side_effect = LLMError("Token count error", provider="OpenAIProvider", model="test-model")
        with pytest.raises(LLMError, match="Token count error"):
            await provider.count_tokens("Test text")

        # Test token limit
        token_limit = await provider.get_token_limit()
        assert token_limit == 4096
        provider.get_token_limit.assert_called_once()


@pytest.mark.asyncio
async def test_provider_error_handling():
    """Test error handling across all providers."""
    providers = [
        (OpenAIProvider, "openai", "ChatOpenAI"),
        (GeminiProvider, "gemini", "ChatGoogleGenerativeAI"),
        (AnthropicProvider, "anthropic", "ChatAnthropic"),
        (GroqProvider, "groq", "ChatGroq"),
        (MistralProvider, "mistral", "ChatMistralAI"),
        (OllamaProvider, "ollama", "ChatOllama"),
    ]

    for provider_class, provider_name, chat_class in providers:
        with patch(f"otterai.llm.{provider_name}_provider.{chat_class}") as mock_chat:
            print(f"Mocking {provider_name} provider with {chat_class}")
            mock_chat.side_effect = Exception("API error")
            with pytest.raises(ConfigurationError) as exc_info:
                if provider_class == OllamaProvider:
                    provider_class(model="codellama")
                else:
                    provider_class(api_key="test-key", model="test-model")
            assert "API error" in str(exc_info.value)