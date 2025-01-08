"""Core models for cori_ai."""
from typing import Any, Dict, List, Optional, Union, Set
from pydantic import BaseModel, Field, ConfigDict, field_validator
from enum import Enum
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage


class BaseOtterModel(BaseModel):
    """Base model with common functionality."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        json_schema_extra={
            "examples": []  # Add examples for better LLM understanding
        }
    )


class CodeReviewComment(BaseOtterModel):
    """Model for code review comments."""
    path: str = Field(
        description="File path where the comment should be added",
        examples=["src/main.py", "lib/utils.js"]
    )
    line: int = Field(
        description="Line number in the file where the comment should be added",
        gt=0,
        examples=[10, 42]
    )
    body: Optional[str] = Field(
        description="The review comment with emoji category and specific feedback",
        default="",
        examples=[
            "🔒 Security: Consider using a secure hash function here",
            "⚡ Performance: This loop could be optimized using list comprehension"
        ]
    )

    @field_validator('line')
    def line_must_be_positive(cls, v: int) -> int:
        """Validate line number is positive."""
        if v <= 0:
            raise ValueError('Line number must be positive')
        return v


class CodeReviewResponse(BaseOtterModel):
    """Model for code review response."""
    comments: List[CodeReviewComment] = Field(
        description="New comments to add",
        examples=[[
            {
                "path": "src/main.py",
                "line": 42,
                "body": "✨ Code Quality: Consider extracting this into a separate function"
            }
        ]]
    )
    comments_to_delete: List[int] = Field(
        description="IDs of comments that should be deleted",
        default=[],
        examples=[[123, 456]]
    )


class CodeFix(BaseOtterModel):
    """Model for code fix response."""
    file: str = Field(
        description="File path that was fixed",
        examples=["src/main.py", "lib/utils.js"]
    )
    content: str = Field(
        description="Complete fixed file content with all necessary imports and dependencies",
        min_length=1,
        examples=[
            '''import json
from typing import Dict

def process_data(data: Dict) -> Dict:
    """Process input data."""
    return {k: v.strip() for k, v in data.items()}'''
        ]
    )

    @field_validator('content')
    def content_not_empty(cls, v: str) -> str:
        """Validate content is not empty."""
        if not v.strip():
            raise ValueError('Content cannot be empty')
        return v


class FileDiff(BaseOtterModel):
    """Model for file diff information."""
    file: str = Field(
        description="File path",
        examples=["src/main.py"]
    )
    patch: Optional[str] = Field(
        description="Git patch content",
        default=None,
        examples=[
            "@@ -1,3 +1,4 @@\n+import json\n def main():\n-    pass\n+    return {}"
        ]
    )
    content: str = Field(
        description="File content",
        examples=[
            "def main():\n    return {}"
        ]
    )
    existing_comments: List[Dict[str, Any]] = Field(
        description="Existing comments on the file",
        default_factory=list,
        examples=[[
            {
                "id": 123,
                "path": "src/main.py",
                "line": 42,
                "body": "Consider adding type hints"
            }
        ]]
    )
    line_mapping: Dict[int, Dict[str, Any]] = Field(
        description="Line number mapping",
        default_factory=dict,
        examples=[{
            "42": {
                "old_line": 40,
                "new_line": 42,
                "content": "    return {}"
            }
        }]
    )


class PullRequestInfo(BaseOtterModel):
    """Model for pull request information."""
    number: int = Field(
        description="PR number",
        examples=[42, 123]
    )
    title: str = Field(
        description="PR title",
        examples=[
            "Add new feature",
            "Fix security vulnerability"
        ]
    )
    body: Optional[str] = Field(
        description="PR description",
        default=None,
        examples=[
            "This PR adds a new feature that:\n- Does X\n- Improves Y\n- Fixes Z"
        ]
    )
    state: str = Field(
        description="PR state (open, closed, merged)",
        examples=["open", "closed", "merged"]
    )
    head_sha: str = Field(
        description="Head commit SHA",
        examples=["abc123def456"]
    )
    head_ref: str = Field(
        description="Head branch name",
        examples=["feature/new-feature"]
    )
    base_ref: str = Field(
        description="Base branch name",
        examples=["main", "develop"]
    )
    user_login: str = Field(
        description="PR author login",
        examples=["johndoe", "alice123"]
    )


class DependencyGraph(BaseModel):
    nodes: Dict[str, Set[str]] = Field(default_factory=dict)
    file_types: Dict[str, str] = Field(default_factory=dict)
    imports: Dict[str, List[str]] = Field(default_factory=dict)
    dependencies: Dict[str, List[str]] = Field(default_factory=dict)
    metadata: Dict[str, Dict] = Field(default_factory=dict)
    edges: List[Dict[str, str]] = Field(default_factory=list)
    clusters: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
