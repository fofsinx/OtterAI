"""Core package for OtterAI."""
from otterai.core.models import (
    BaseOtterModel,
    CodeReviewComment,
    CodeReviewResponse,
    CodeFix,
    FileDiff,
    PullRequestInfo,
)
from otterai.core.config import settings, EMOJI_MAP
from otterai.core.exceptions import (
    OtterAIError,
    ConfigurationError,
    GitHubError,
    LLMError,
    ReviewError,
    FixGenerationError,
    ValidationError,
    RateLimitError,
    AuthenticationError,
    ParseError,
    TimeoutError,
)

__all__ = [
    # Models
    'BaseOtterModel',
    'CodeReviewComment',
    'CodeReviewResponse',
    'CodeFix',
    'FileDiff',
    'PullRequestInfo',
    
    # Config
    'settings',
    'EMOJI_MAP',
    
    # Exceptions
    'OtterAIError',
    'ConfigurationError',
    'GitHubError',
    'LLMError',
    'ReviewError',
    'FixGenerationError',
    'ValidationError',
    'RateLimitError',
    'AuthenticationError',
    'ParseError',
    'TimeoutError',
] 