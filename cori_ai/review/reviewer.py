"""Code review module for cori_ai."""
import re
from typing import List, Dict, Any, Optional, AsyncGenerator
import json

from cori_ai.core.exceptions import ReviewError
from cori_ai.core.config import settings, EMOJI_MAP
from cori_ai.core.models import CodeReviewComment, CodeReviewResponse, FileDiff
from cori_ai.llm import get_provider
from cori_ai.github import GitHubClient


class CodeReviewer:
    """Code reviewer that uses LLM to generate review comments."""

    def __init__(self, github_client: GitHubClient):
        """Initialize the code reviewer.
        
        Args:
            github_client: GitHub client instance.
        """
        self.github = github_client
        self.llm = get_provider(settings.provider)

    async def review_pull_request(
            self,
            owner: str,
            repo: str,
            number: int,
    ) -> AsyncGenerator[CodeReviewResponse, None]:
        """Review a pull request.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            number: Pull request number.
            
        Yields:
            Review responses for each file.
            
        Raises:
            ReviewError: If review fails.
        """
        try:
            pr = await self.github.get_pull_request(owner, repo, number)

            # Check if PR should be skipped
            if self._should_skip_review(pr.title, pr.state):
                return

            async for file_diff in self.github.get_pull_request_files(owner, repo, number):
                if not file_diff.patch:
                    continue  # Skip files without changes

                try:
                    review = await self._review_file(file_diff)
                    if review.comments:
                        yield review
                except Exception as e:
                    raise ReviewError(
                        f"Failed to review file {file_diff.file}: {str(e)}",
                        file=file_diff.file,
                    )

        except Exception as e:
            raise ReviewError(f"Failed to review PR: {str(e)}")

    @staticmethod
    def _should_skip_review(title: str, state: str) -> bool:
        """Check if PR should be skipped based on title and state.
        
        Args:
            title: PR title.
            state: PR state.
            
        Returns:
            True if PR should be skipped.
        """
        # Check title patterns
        for pattern in settings.skip_title_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                return True

        # Check state patterns
        for pattern in settings.skip_state_patterns:
            if re.search(pattern, state, re.IGNORECASE):
                return True

        return False

    async def _review_file(self, file_diff: FileDiff) -> CodeReviewResponse:
        """Review a single file.
        
        Args:
            file_diff: File diff information.
            
        Returns:
            Review response.
            
        Raises:
            ReviewError: If review fails.
        """
        # Prepare review prompt
        prompt = self._build_review_prompt(file_diff)

        # Get review from LLM
        try:
            response = await self.llm.generate_json(
                prompt,
                json_schema={
                    "type": "object",
                    "properties": {
                        "comments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "line": {"type": "integer"},
                                    "category": {"type": "string"},
                                    "message": {"type": "string"},
                                },
                                "required": ["line", "category", "message"],
                            },
                        },
                    },
                    "required": ["comments"],
                },
            )
        except Exception as e:
            raise ReviewError(f"Failed to generate review: {str(e)}")

        # Convert LLM response to CodeReviewResponse
        comments = []
        for comment in response["comments"]:
            # Skip comments on lines that don't exist in the mapping
            if comment["line"] not in file_diff.line_mapping:
                continue

            # Format comment with emoji
            emoji = EMOJI_MAP.get(comment["category"], "💡")
            body = f"{emoji} {comment['message']}"

            comments.append(
                CodeReviewComment(
                    path=file_diff.file,
                    line=comment["line"],
                    body=body,
                )
            )

        return CodeReviewResponse(comments=comments)

    @staticmethod
    def _build_review_prompt(file_diff: FileDiff) -> str:
        """Build prompt for file review.
        
        Args:
            file_diff: File diff information.
            
        Returns:
            Review prompt.
        """
        prompt = f"""Review the following code changes and provide feedback.
Focus on:
- Security issues
- Performance improvements
- Code quality and maintainability
- Test coverage
- Documentation

File: {file_diff.file}
Patch:
{file_diff.patch}

Existing comments:
{json.dumps(file_diff.existing_comments, indent=2)}

{settings.extra_prompt}

Provide feedback in JSON format with an array of comments.
Each comment should have:
- line: The line number to comment on
- category: One of [security, performance, maintainability, code_quality, test_coverage]
- message: The review comment (without emoji)

Example:
{{
    "comments": [
        {{
            "line": 42,
            "category": "security",
            "message": "This SQL query is vulnerable to injection attacks. Use parameterized queries instead."
        }}
    ]
}}"""
        return prompt
