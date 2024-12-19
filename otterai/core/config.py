"""Configuration settings for OtterAI."""
import os
from typing import Dict, List, Optional, Union
from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from langchain.callbacks import StdOutCallbackHandler
from langchain.callbacks.manager import CallbackManager
from langchain_core.globals import set_verbose, set_debug

# Create callback manager
callback_manager = CallbackManager([StdOutCallbackHandler()])

class OtterAISettings(BaseSettings):
    """OtterAI configuration settings."""
    model_config = ConfigDict(
        env_prefix="INPUT_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"
    )

    # LLM Provider Settings
    provider: str = Field(
        default="openai",
        description="LLM provider to use (openai, gemini, anthropic, groq, mistral, ollama)"
    )
    model: Optional[str] = Field(
        default=None,
        description="Model to use (provider-specific)"
    )

    # Callback Manager
    callback_manager: CallbackManager = Field(
        default_factory=lambda: CallbackManager([StdOutCallbackHandler()]),
        description="LangChain callback manager"
    )

    # API Keys
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API base URL"
    )
    google_api_key: Optional[str] = Field(default=None, description="Google API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    groq_api_key: Optional[str] = Field(default=None, description="Groq API key")
    mistral_api_key: Optional[str] = Field(default=None, description="Mistral API key")

    # Ollama Settings
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL"
    )
    ollama_model: str = Field(
        default="codellama",
        description="Default Ollama model to use"
    )
    ollama_num_gpu: int = Field(
        default=1,
        description="Number of GPUs to use for Ollama"
    )
    ollama_num_thread: int = Field(
        default=8,
        description="Number of CPU threads to use for Ollama"
    )

    # GitHub Settings
    github_token: str = Field(description="GitHub token for PR access")
    skip_fixes: bool = Field(default=False, description="Skip fix generation")
    skip_generated_pr_review: bool = Field(default=True, description="Skip generated PR review")

    # Review Settings
    extra_prompt: str = Field(default="", description="Additional instructions for the AI reviewer")

    # Default Models by Provider
    default_models: Dict[str, str] = Field(
        default={
            "openai": "gpt-4-turbo-preview",
            "gemini": "gemini-1.5-flash",
            "anthropic": "claude-3-opus",
            "groq": "mixtral-8x7b-32768",
            "mistral": "mistral-large-latest",
            "ollama": "codellama",
        }
    )

    # Skip Patterns
    skip_title_patterns: List[str] = Field(
        default=[
            r"(no|skip)(-|\s)?review",
            r"skip(-|\s)?code(-|\s)?review",
            r"otter(ai)?(-|\s)?skip",
            r"otter(-|\s)?restricted"
        ]
    )
    skip_state_patterns: List[str] = Field(
        default=[
            r"merged",
            r"closed"
        ]
    )

    # Branch Patterns
    fix_branch_pattern: str = Field(
        default=r"otterai/fixes-for-pr-\d+",
        description="Pattern for fix branches"
    )

    # Retry Settings
    max_retries: int = Field(default=3, description="Maximum number of retries for API calls")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")

    # Logging Settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(levelname)s - %(message)s",
        description="Logging format"
    )

    # LangChain Settings
    langchain_verbose: bool = Field(default=False, description="Enable LangChain verbose mode")
    langchain_debug: bool = Field(default=False, description="Enable LangChain debug mode")
    langchain_tracing: bool = Field(default=False, description="Enable LangChain tracing")
    langchain_project: str = Field(default="otterai", description="LangChain project name")
    langchain_callbacks: List[str] = Field(
        default=["console"],
        description="LangChain callbacks to enable (console, langchain)",
    )

    def get_model_for_provider(self) -> str:
        """Get the appropriate model for the current provider."""
        if self.model:
            return self.model
        return self.default_models.get(self.provider, self.default_models["openai"])

    def setup_langchain(self) -> CallbackManager:
        """Setup LangChain configuration."""
        callbacks: List[StdOutCallbackHandler] = []
        
        # Add stdout handler for verbose mode
        if self.langchain_verbose:
            callbacks.append(StdOutCallbackHandler())
            set_verbose(True)
        
        # Add debug handler
        if self.langchain_debug:
            callbacks.append(StdOutCallbackHandler())
            set_debug(True)
        
        return CallbackManager(callbacks)


# Constants
EMOJI_MAP = {
    "security": "🔒",
    "performance": "⚡",
    "maintainability": "🔧",
    "code_quality": "✨",
    "test_coverage": "🧪",
    "documentation": "📝",
    "bug": "🐛",
    "feature": "✨",
    "refactor": "♻️",
    "style": "🎨",
    "test": "✅",
    "chore": "🔧",
    "ci": "👷",
    "revert": "⏪",
}

# Create a global settings instance
settings = OtterAISettings()

# Initialize LangChain with settings
callback_manager = settings.setup_langchain()
