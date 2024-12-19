"""Base LLM provider interface."""
from typing import Any, Dict, Optional, AsyncGenerator
from abc import ABC, abstractmethod

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from otterai.core.exceptions import LLMError, ConfigurationError
from otterai.core.config import settings


class BaseLLMProvider(ABC):
    """Base class for LLM providers using LangChain."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize the LLM provider.
        
        Args:
            api_key: Optional API key. If not provided, will be taken from settings.
            model: Optional model name. If not provided, will use provider's default.
            
        Raises:
            ConfigurationError: If initialization fails.
        """
        try:
            self.api_key = api_key
            self.model = model or settings.get_model_for_provider()
            self._llm: Optional[BaseChatModel] = None
            # Initialize LLM immediately to catch configuration errors
            _ = self.llm
        except Exception as e:
            raise ConfigurationError(f"Provider initialization failed: {str(e)}", provider=self.__class__.__name__)

    @property
    @abstractmethod
    def llm(self) -> BaseChatModel:
        """Get the LangChain chat model instance.
        
        Returns:
            LangChain chat model.
            
        Raises:
            ConfigurationError: If model initialization fails.
        """
        pass

    async def generate(
            self,
            prompt: str,
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            stop: Optional[list[str]] = None,
            **kwargs: Any,
    ) -> str:
        """Generate text from the LLM.
        
        Args:
            prompt: The prompt to generate from.
            temperature: Sampling temperature (0.0 to 1.0).
            max_tokens: Maximum number of tokens to generate.
            stop: Optional list of strings that will stop generation.
            **kwargs: Additional provider-specific arguments.
            
        Returns:
            Generated text string.
            
        Raises:
            LLMError: If generation fails.
        """
        try:
            messages = [HumanMessage(content=prompt)]
            response = await self.llm.ainvoke(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop,
                **kwargs
            )
            return response.content
        except Exception as e:
            raise LLMError(f"Generation failed: {str(e)}", provider=self.__class__.__name__, model=self.model)

    async def generate_json(
            self,
            prompt: str,
            json_schema: Dict[str, Any],
            temperature: float = 0.2,
            **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate JSON output from the LLM.
        
        Args:
            prompt: The prompt to generate from.
            json_schema: JSON schema defining the expected output format.
            temperature: Sampling temperature (0.0 to 1.0).
            **kwargs: Additional provider-specific arguments.
            
        Returns:
            Generated JSON object matching the schema.
            
        Raises:
            LLMError: If generation or JSON parsing fails.
        """
        try:
            # Create parser and prompt template
            parser = JsonOutputParser(pydantic_object=json_schema)
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", "You are a structured data generator. Output must be valid JSON matching the schema."),
                ("user", "{input}\n\nSchema: {schema}")
            ])

            # Create chain
            chain = (
                {"input": RunnablePassthrough(), "schema": lambda _: json_schema}
                | prompt_template
                | self.llm
                | parser
            )

            # Run chain
            response = await chain.ainvoke(
                prompt,
                config={"temperature": temperature, **kwargs}
            )
            return response
        except Exception as e:
            raise LLMError(f"JSON generation failed: {str(e)}", provider=self.__class__.__name__, model=self.model)

    async def stream(
            self,
            prompt: str,
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            stop: Optional[list[str]] = None,
            **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Stream text from the LLM.
        
        Args:
            prompt: The prompt to generate from.
            temperature: Sampling temperature (0.0 to 1.0).
            max_tokens: Maximum number of tokens to generate.
            stop: Optional list of strings that will stop generation.
            **kwargs: Additional provider-specific arguments.
            
        Yields:
            Generated text chunks.
            
        Raises:
            LLMError: If streaming fails.
        """
        try:
            messages = [HumanMessage(content=prompt)]
            async for chunk in self.llm.astream(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop,
                **kwargs
            ):
                yield chunk.content
        except Exception as e:
            raise LLMError(f"Streaming failed: {str(e)}", provider=self.__class__.__name__, model=self.model)

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string.
        
        Args:
            text: Text to count tokens for.
            
        Returns:
            Number of tokens.
            
        Raises:
            LLMError: If token counting fails.
        """
        try:
            return self.llm.get_num_tokens(text)
        except Exception as e:
            raise LLMError(f"Token counting failed: {str(e)}", provider=self.__class__.__name__, model=self.model)

    def get_token_limit(self) -> int:
        """Get the maximum number of tokens supported by the model.
        
        Returns:
            Maximum token limit.
            
        Raises:
            LLMError: If getting token limit fails.
        """
        try:
            return self.llm.modelname_to_contextsize(self.model)
        except Exception as e:
            raise LLMError(f"Failed to get token limit: {str(e)}", provider=self.__class__.__name__, model=self.model)

    @property
    def model_name(self) -> str:
        """Get the model name.
        
        Returns:
            Model name string.
        """
        return self.model

    @property
    def model_info(self) -> Dict[str, Any]:
        """Get the model info."""
        return self.llm.get_model_info(self.model)
