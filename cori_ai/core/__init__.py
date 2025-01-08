"""Core package for cori_ai."""
from cori_ai.core.models import (
    BaseOtterModel,
    CodeReviewComment,
    CodeReviewResponse,
    CodeFix,
    FileDiff,
    PullRequestInfo,
)
from cori_ai.core.config import settings, EMOJI_MAP
from cori_ai.core.exceptions import (
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