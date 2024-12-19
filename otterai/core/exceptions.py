"""Custom exceptions for OtterAI."""


class OtterAIError(Exception):
    """Base exception for OtterAI."""
    pass


class ConfigurationError(OtterAIError):
    """Raised when there's a configuration error."""

    def __init__(self, message: str, provider: str = None):
        self.provider = provider
        super().__init__(message)


class GitHubError(OtterAIError):
    """Raised when there's a GitHub API error."""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class LLMError(OtterAIError):
    """Raised when there's an LLM-related error."""

    def __init__(self, message: str, provider: str = None, model: str = None):
        self.provider = provider
        self.model = model
        super().__init__(message)


class ReviewError(OtterAIError):
    """Raised when there's an error during code review."""

    def __init__(self, message: str, file: str = None, line: int = None):
        self.file = file
        self.line = line
        super().__init__(message)


class FixGenerationError(OtterAIError):
    """Raised when there's an error generating fixes."""

    def __init__(self, message: str, file: str = None):
        self.file = file
        super().__init__(message)


class ValidationError(OtterAIError):
    """Raised when there's a validation error."""

    def __init__(self, message: str, field: str = None, value: str = None):
        self.field = field
        self.value = value
        super().__init__(message)


class RateLimitError(OtterAIError):
    """Raised when rate limits are hit."""

    def __init__(self, message: str, reset_time: int = None):
        self.reset_time = reset_time
        super().__init__(message)


class AuthenticationError(OtterAIError):
    """Raised when there's an authentication error."""
    pass


class ParseError(OtterAIError):
    """Raised when there's a parsing error."""

    def __init__(self, message: str, raw_content: str = None):
        self.raw_content = raw_content
        super().__init__(message)


class TimeoutError(OtterAIError):
    """Raised when an operation times out."""
    pass
