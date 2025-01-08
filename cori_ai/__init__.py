"""CoriAI - AI-powered code review and fix generation."""
from cori_ai.core import (
    settings,
    EMOJI_MAP,
    CodeReviewComment,
    CodeReviewResponse,
    CodeFix,
    FileDiff,
    PullRequestInfo,
)
from cori_ai.github import GitHubClient
from cori_ai.review import CodeReviewer
from cori_ai.fix import FixGenerator

__version__ = "0.1.0"

__all__ = [
    # Core
    'settings',
    'EMOJI_MAP',
    'CodeReviewComment',
    'CodeReviewResponse',
    'CodeFix',
    'FileDiff',
    'PullRequestInfo',

    # GitHub
    'GitHubClient',

    # Review
    'CodeReviewer',

    # Fix
    'FixGenerator',

    # Version
    '__version__',
]
