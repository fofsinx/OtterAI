"""Tests for configuration settings."""
import os
from unittest.mock import patch
import pytest

from cori_ai.core.config import OtterAISettings, settings, EMOJI_MAP


@pytest.fixture
def clean_env():
    """Fixture to provide a clean environment."""
    original_env = dict(os.environ)
    os.environ.clear()
    os.environ["INPUT_PROVIDER"] = "openai"  # Set default provider
    os.environ["INPUT_MODEL"] = ""  # Clear model setting
    os.environ["INPUT_EXTRA_PROMPT"] = ""  # Clear extra prompt
    yield
    os.environ.clear()
    os.environ.update(original_env)


def test_settings_defaults(clean_env):
    """Test that default settings are correctly set."""
    config = OtterAISettings()  # Create new instance with clean environment
    assert config.provider == "openai"
    assert config.model == "" or config.model is None  # Allow either empty string or None
    assert config.extra_prompt == ""
    assert config.skip_fixes is False
    assert config.skip_generated_pr_review is True
    assert config.log_level == "INFO"
    assert config.langchain_project == "otterai"


def test_get_model_for_provider(clean_env):
    """Test model selection for providers."""
    config = OtterAISettings()

    # Test with custom model
    config.model = "custom-model"
    assert config.get_model_for_provider() == "custom-model"

    # Test with default models
    config.model = None
    for provider, model in config.default_models.items():
        config.provider = provider
        assert config.get_model_for_provider() == model


def test_setup_langchain(clean_env):
    """Test LangChain configuration setup."""
    config = OtterAISettings()

    # Test default setup
    callback_manager = config.setup_langchain()
    assert callback_manager is not None
    assert len(callback_manager.handlers) == 0

    # Test verbose mode
    config.langchain_verbose = True
    callback_manager = config.setup_langchain()
    assert len(callback_manager.handlers) == 1

    # Test debug mode
    config.langchain_debug = True
    callback_manager = config.setup_langchain()
    assert len(callback_manager.handlers) == 2


def test_emoji_map():
    """Test emoji mapping."""
    assert EMOJI_MAP["security"] == "🔒"
    assert EMOJI_MAP["performance"] == "⚡"
    assert EMOJI_MAP["maintainability"] == "🔧"
    assert EMOJI_MAP["code_quality"] == "✨"
    assert EMOJI_MAP["test_coverage"] == "🧪"


@pytest.mark.parametrize("env_var,value,expected", [
    ("INPUT_PROVIDER", "gemini", "gemini"),
    ("INPUT_MODEL", "custom-model", "custom-model"),
    ("INPUT_OPENAI_API_KEY", "test-key", "test-key"),
    ("INPUT_SKIP_FIXES", "true", True),
    ("INPUT_MAX_RETRIES", "5", 5),
    ("INPUT_LOG_LEVEL", "DEBUG", "DEBUG"),
])
def test_environment_variables(clean_env, env_var, value, expected):
    """Test environment variable handling."""
    with patch.dict(os.environ, {env_var: value}):
        config = OtterAISettings()
        assert getattr(config, env_var.replace("INPUT_", "").lower()) == expected


def test_global_settings():
    """Test global settings instance."""
    assert isinstance(settings, OtterAISettings)
    assert settings.model_config.get("env_prefix") == "INPUT_"
    assert settings.model_config.get("case_sensitive") is False
    assert settings.model_config.get("env_file") == ".env"
    assert settings.model_config.get("env_file_encoding") == "utf-8"
    assert settings.model_config.get("extra") == "allow"
  