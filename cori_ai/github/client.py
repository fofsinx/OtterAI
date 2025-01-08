"""GitHub API client for cori_ai."""
import re
from typing import List, Dict, Any, Optional, AsyncGenerator
import asyncio
import base64
from github import Github
from cori_ai.core.exceptions import GitHubError, AuthenticationError
from cori_ai.core.config import settings
from cori_ai.core.models import PullRequestInfo, FileDiff


class GitHubClient:
    """GitHub API client using PyGitHub."""

    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com"):
        """Initialize the GitHub client.
        
        Args:
            token: GitHub token. If not provided, will be taken from settings.
            base_url: GitHub API base URL.
        """
        self.token = token or settings.github_token
        if not self.token:
            raise AuthenticationError("GitHub token not provided")

        self.github = Github(
            login_or_token=self.token,
            base_url=base_url,
            timeout=30,
            retry=settings.max_retries,
        )

    async def __aenter__(self):
        """Enter async context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        await asyncio.to_thread(self.github.close)

    async def get_pull_request(self, owner: str, repo: str, number: int) -> PullRequestInfo:
        """Get pull request information."""
        try:
            def _get_pr():
                repository = self.github.get_repo(f"{owner}/{repo}")
                pr = repository.get_pull(number)
                return PullRequestInfo(
                    number=pr.number,
                    title=pr.title,
                    body=pr.body,
                    state=pr.state,
                    head_sha=pr.head.sha,
                    head_ref=pr.head.ref,
                    base_ref=pr.base.ref,
                    user_login=pr.user.login,
                )
            return await asyncio.to_thread(_get_pr)
        except Exception as e:
            raise GitHubError(f"Failed to get PR: {str(e)}")

    async def get_pull_request_files(
            self,
            owner: str,
            repo: str,
            number: int,
    ) -> AsyncGenerator[FileDiff, None]:
        """Get files changed in a pull request."""
        try:
            repository = await asyncio.to_thread(self.github.get_repo, f"{owner}/{repo}")
            pr = await asyncio.to_thread(repository.get_pull, number)
            files = await asyncio.to_thread(list, pr.get_files())
            
            for file in files:
                # Get file content and comments concurrently
                content, comments = await asyncio.gather(
                    self.get_file_content(owner, repo, file.filename, file.sha),
                    self.get_file_comments(owner, repo, number, file.filename)
                )
                
                yield FileDiff(
                    file=file.filename,
                    patch=file.patch,
                    content=content,
                    existing_comments=comments,
                    line_mapping=self._build_line_mapping(file.patch),
                )
        except Exception as e:
            raise GitHubError(f"Failed to get PR files: {str(e)}")

    async def get_file_content(
            self,
            owner: str,
            repo: str,
            path: str,
            ref: str,
    ) -> str:
        """Get file content at a specific ref."""
        try:
            def _get_content():
                repository = self.github.get_repo(f"{owner}/{repo}")
                try:
                    content_file = repository.get_contents(path, ref=ref)
                    if isinstance(content_file, list):
                        raise GitHubError(f"Path {path} is a directory")
                    return base64.b64decode(content_file.content).decode('utf-8')
                except Exception as e:
                    if "404" in str(e):
                        return ""  # New file
                    raise
            return await asyncio.to_thread(_get_content)
        except Exception as e:
            raise GitHubError(f"Failed to get file content: {str(e)}")

    async def get_file_comments(
            self,
            owner: str,
            repo: str,
            number: int,
            path: str,
    ) -> List[Dict[str, Any]]:
        """Get review comments on a file."""
        try:
            def _get_comments():
                repository = self.github.get_repo(f"{owner}/{repo}")
                pr = repository.get_pull(number)
                comments = []
                for comment in pr.get_comments():
                    if comment.path == path:
                        comments.append({
                            "id": comment.id,
                            "path": comment.path,
                            "line": comment.position,
                            "body": comment.body,
                            "user": comment.user.login,
                        })
                return comments
            return await asyncio.to_thread(_get_comments)
        except Exception as e:
            raise GitHubError(f"Failed to get file comments: {str(e)}")

    async def create_review_comment(
            self,
            owner: str,
            repo: str,
            number: int,
            body: str,
            commit_id: str,
            path: str,
            line: int,
    ) -> Dict[str, Any]:
        """Create a review comment."""
        try:
            def _create_comment():
                repository = self.github.get_repo(f"{owner}/{repo}")
                pr = repository.get_pull(number)
                get_commit = repository.get_commit(commit_id)
                comment = pr.create_review_comment(
                    body=body,
                    commit=get_commit,
                    path=path,
                    line=line,
                    side="RIGHT",
                )
                return {
                    "id": comment.id,
                    "path": comment.path,
                    "line": comment.position,
                    "body": comment.body,
                    "user": comment.user.login,
                }
            return await asyncio.to_thread(_create_comment)
        except Exception as e:
            raise GitHubError(f"Failed to create review comment: {str(e)}")

    async def delete_review_comment(
            self,
            owner: str,
            repo: str,
            comment_id: int,
    ) -> None:
        """Delete a review comment."""
        try:
            def _delete_comment():
                repository = self.github.get_repo(f"{owner}/{repo}")
                comment = repository.get_comment(comment_id)
                comment.delete()
            await asyncio.to_thread(_delete_comment)
        except Exception as e:
            raise GitHubError(f"Failed to delete review comment: {str(e)}")

    async def create_branch(
            self,
            owner: str,
            repo: str,
            branch: str,
            sha: str,
    ) -> None:
        """Create a new branch."""
        try:
            def _create_branch():
                repository = self.github.get_repo(f"{owner}/{repo}")
                repository.create_git_ref(f"refs/heads/{branch}", sha)
            await asyncio.to_thread(_create_branch)
        except Exception as e:
            raise GitHubError(f"Failed to create branch: {str(e)}")

    async def create_commit(
            self,
            owner: str,
            repo: str,
            branch: str,
            message: str,
            changes: List[Dict[str, str]],
    ) -> None:
        """Create a commit with file changes."""
        try:
            def _create_commit():
                repository = self.github.get_repo(f"{owner}/{repo}")
                ref = repository.get_git_ref(f"heads/{branch}")
                base_tree = repository.get_git_tree(ref.object.sha)
                
                # Create blobs and tree entries
                element_list = []
                for change in changes:
                    blob = repository.create_git_blob(change["content"], "utf-8")
                    element = {
                        "path": change["file"],
                        "mode": "100644",
                        "type": "blob",
                        "sha": blob.sha,
                    }
                    element_list.append(element)
                
                # Create tree
                tree = repository.create_git_tree(element_list, base_tree)
                
                # Create commit
                parent = repository.get_git_commit(ref.object.sha)
                commit = repository.create_git_commit(message, tree, [parent])
                
                # Update reference
                ref.edit(commit.sha)
            await asyncio.to_thread(_create_commit)
        except Exception as e:
            raise GitHubError(f"Failed to create commit: {str(e)}")

    async def create_pull_request(
            self,
            owner: str,
            repo: str,
            title: str,
            body: str,
            head: str,
            base: str,
    ) -> Dict[str, Any]:
        """Create a pull request."""
        try:
            def _create_pr():
                repository = self.github.get_repo(f"{owner}/{repo}")
                pr = repository.create_pull(
                    title=title,
                    body=body,
                    head=head,
                    base=base,
                )
                return {
                    "number": pr.number,
                    "title": pr.title,
                    "body": pr.body,
                    "state": pr.state,
                    "head_sha": pr.head.sha,
                    "head_ref": pr.head.ref,
                    "base_ref": pr.base.ref,
                    "user_login": pr.user.login,
                }
            return await asyncio.to_thread(_create_pr)
        except Exception as e:
            raise GitHubError(f"Failed to create PR: {str(e)}")

    @staticmethod
    def _build_line_mapping(patch: Optional[str]) -> Dict[int, Dict[str, Any]]:
        """Build mapping of new line numbers to original line numbers from patch."""
        if not patch:
            return {}

        mapping = {}
        current_line = 0
        for line in patch.split("\n"):
            if line.startswith("@@"):
                # Parse hunk header
                match = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
                if match:
                    current_line = int(match.group(1)) - 1
            elif not line.startswith("-"):
                current_line += 1
                if not line.startswith("+"):
                    mapping[current_line] = {"original_line": current_line}

        return mapping
