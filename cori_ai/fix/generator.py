"""Fix generator module for cori_ai."""
from typing import List, Dict, Any, Optional, AsyncGenerator
import json

from cori_ai.core.exceptions import FixGenerationError
from cori_ai.core.config import settings
from cori_ai.core.models import CodeFix, FileDiff
from cori_ai.llm import get_provider
from cori_ai.github import GitHubClient


class FixGenerator:
    """Fix generator that uses LLM to generate code fixes."""

    def __init__(self, github_client: GitHubClient):
        """Initialize the fix generator.
        
        Args:
            github_client: GitHub client instance.
        """
        self.github = github_client
        self.llm = get_provider(settings.provider)

    async def generate_fixes(
            self,
            owner: str,
            repo: str,
            number: int,
            comments: List[Dict[str, Any]],
    ) -> AsyncGenerator[CodeFix, None]:
        """Generate fixes for review comments.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            number: Pull request number.
            comments: List of review comments.
            
        Yields:
            Generated fixes.
            
        Raises:
            FixGenerationError: If fix generation fails.
        """
        if settings.skip_fixes:
            return

        try:
            # Group comments by file
            files_to_fix = {}
            for comment in comments:
                path = comment["path"]
                if path not in files_to_fix:
                    files_to_fix[path] = []
                files_to_fix[path].append(comment)

            # Get file diffs
            async for file_diff in self.github.get_pull_request_files(owner, repo, number):
                if file_diff.file not in files_to_fix:
                    continue

                try:
                    fix = await self._generate_fix(
                        file_diff,
                        files_to_fix[file_diff.file],
                    )
                    if fix:
                        yield fix
                except Exception as e:
                    raise FixGenerationError(
                        f"Failed to generate fix for {file_diff.file}: {str(e)}",
                        file=file_diff.file,
                    )

        except Exception as e:
            raise FixGenerationError(f"Failed to generate fixes: {str(e)}")

    async def _generate_fix(
            self,
            file_diff: FileDiff,
            comments: List[Dict[str, Any]],
    ) -> Optional[CodeFix]:
        """Generate fix for a single file.
        
        Args:
            file_diff: File diff information.
            comments: List of review comments for the file.
            
        Returns:
            Generated fix or None if no fix is needed.
            
        Raises:
            FixGenerationError: If fix generation fails.
        """
        # Prepare fix prompt
        prompt = self._build_fix_prompt(file_diff, comments)

        # Get fix from LLM
        try:
            response = await self.llm.generate_json(
                prompt,
                json_schema={
                    "type": "object",
                    "properties": {
                        "fixed_content": {"type": "string"},
                        "changes_made": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["fixed_content", "changes_made"],
                },
            )
        except Exception as e:
            raise FixGenerationError(f"Failed to generate fix: {str(e)}")

        # Skip if no changes were made
        if not response["changes_made"]:
            return None

        return CodeFix(
            file=file_diff.file,
            content=response["fixed_content"],
        )

    @staticmethod
    def _build_fix_prompt(
            file_diff: FileDiff,
            comments: List[Dict[str, Any]],
    ) -> str:
        """Build prompt for fix generation.

        Args:
            file_diff: File diff information.
            comments: List of review comments.

        Returns:
            Fix prompt.
        """
        prompt = f"""Fix the following code based on review comments.

File: {file_diff.file}
Content:
{file_diff.content}

Review comments:
{json.dumps(comments, indent=2)}

{settings.extra_prompt}

Provide the fixed code and a list of changes made in JSON format:
{{
    "fixed_content": "Complete fixed file content with all necessary imports and dependencies",
    "changes_made": [
        "Description of each change made"
    ]
}}

Example: {{ "fixed_content": "import os\\n\\ndef get_user(user_id: int) -> dict:\\n    query = 'SELECT * FROM users 
WHERE id = %s'\\n    return db.execute(query, (user_id,))\\n", "changes_made": [ "Added type hints for better code 
quality", "Fixed SQL injection vulnerability by using parameterized query" ] }}"""
        return prompt
