"""OtterAI - AI-powered code review and fix generation."""
from otterai.core import (
    settings,
    EMOJI_MAP,
    CodeReviewComment,
    CodeReviewResponse,
    CodeFix,
    FileDiff,
    PullRequestInfo,
)
from otterai.github import GitHubClient
from otterai.review import CodeReviewer
from otterai.fix import FixGenerator

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
