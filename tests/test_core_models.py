"""Tests for core models."""
import pytest
from pydantic import ValidationError
from langchain_core.messages import SystemMessage, HumanMessage

from cori_ai.core.models import (
    BaseOtterModel,
    CodeReviewComment,
    CodeReviewResponse,
    CodeFix,
    FileDiff,
    PullRequestInfo,
)


def test_code_review_comment_validation():
    """Test CodeReviewComment validation."""
    # Valid comment
    comment = CodeReviewComment(
        path="src/main.py",
        line=42,
        body="🔒 Security: Consider using a secure hash function here"
    )
    assert comment.path == "src/main.py"
    assert comment.line == 42
    assert comment.body.startswith("🔒 Security")

    # Invalid line number
    with pytest.raises(ValidationError):
        CodeReviewComment(path="src/main.py", line=0)
    
    with pytest.raises(ValidationError):
        CodeReviewComment(path="src/main.py", line=-1)

    # Empty body is allowed
    comment = CodeReviewComment(path="src/main.py", line=1)
    assert comment.body == ""


def test_code_review_response_validation():
    """Test CodeReviewResponse validation."""
    # Valid response with comments
    response = CodeReviewResponse(
        comments=[
            CodeReviewComment(
                path="src/main.py",
                line=42,
                body="✨ Code Quality: Consider extracting this into a function"
            ),
            CodeReviewComment(
                path="src/utils.py",
                line=10,
                body="⚡ Performance: This loop could be optimized"
            )
        ],
        comments_to_delete=[123, 456]
    )
    assert len(response.comments) == 2
    assert len(response.comments_to_delete) == 2

    # Empty comments list is valid
    response = CodeReviewResponse(comments=[])
    assert len(response.comments) == 0
    assert len(response.comments_to_delete) == 0


def test_code_fix_validation():
    """Test CodeFix validation."""
    # Valid fix
    fix = CodeFix(
        file="src/main.py",
        content="""import json
from typing import Dict

def process_data(data: Dict) -> Dict:
    # Process input data.
    return {k: v.strip() for k, v in data.items()}"""
    )
    assert fix.file == "src/main.py"
    assert "process_data" in fix.content

    # Empty content is not allowed (will be caught by pydantic)
    with pytest.raises(ValidationError):
        CodeFix(file="src/main.py", content="")


def test_file_diff_validation():
    """Test FileDiff validation."""
    # Valid diff with all fields
    diff = FileDiff(
        file="src/main.py",
        patch="@@ -1,3 +1,4 @@\n+import json\n def main():\n-    pass\n+    return {}",
        content="def main():\n    return {}",
        existing_comments=[
            {
                "id": 123,
                "path": "src/main.py",
                "line": 42,
                "body": "Consider adding type hints"
            }
        ],
        line_mapping={
            "42": {
                "old_line": 40,
                "new_line": 42,
                "content": "    return {}"
            }
        }
    )
    assert diff.file == "src/main.py"
    assert diff.patch is not None
    assert len(diff.existing_comments) == 1
    assert len(diff.line_mapping) == 1

    # Valid diff without optional fields
    diff = FileDiff(
        file="src/main.py",
        content="def main():\n    return {}"
    )
    assert diff.patch is None
    assert len(diff.existing_comments) == 0
    assert len(diff.line_mapping) == 0


def test_pull_request_info_validation():
    """Test PullRequestInfo validation."""
    # Valid PR info with all fields
    pr = PullRequestInfo(
        number=42,
        title="Add new feature",
        body="This PR adds a new feature that:\n- Does X\n- Improves Y\n- Fixes Z",
        state="open",
        head_sha="abc123def456",
        head_ref="feature/new-feature",
        base_ref="main",
        user_login="johndoe"
    )
    assert pr.number == 42
    assert pr.title == "Add new feature"
    assert pr.body is not None
    assert pr.state == "open"

    # Valid PR info without optional body
    pr = PullRequestInfo(
        number=123,
        title="Fix bug",
        state="closed",
        head_sha="xyz789",
        head_ref="fix/bug",
        base_ref="develop",
        user_login="alice123"
    )
    assert pr.number == 123
    assert pr.body is None
    assert pr.state == "closed"