import os
from typing import List, Dict, Any, Optional, Tuple
from github import Github, PullRequest, PullRequestComment, Repository
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, field_validator
from cori_ai.indexer import generate_review_context
from dotenv import load_dotenv
from cori_ai.llm_client import LLMClient  # Import the singleton client
import re
import threading
import json
import logging

load_dotenv()

lock = threading.Lock()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CodeReviewComment(BaseModel):
    path: str = Field(description="File path where the comment should be added")
    line: int = Field(description="Line number in the file where the comment should be added", gt=0)
    body: Optional[str] = Field(description="The review comment with emoji category and specific feedback", default="")

    @field_validator('line')
    def line_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Line number must be positive')
        return v

class CodeReviewResponse(BaseModel):
    comments: List[CodeReviewComment] = Field(description="New comments to add")
    comments_to_delete: List[int] = Field(description="IDs of comments that should be deleted", default=[])

def validate_comment_position(file_patch: str, line: int) -> bool:
    """Validate if a line number is valid for commenting."""
    if not file_patch:
        return False
        
    current_line = 0
    hunk_start = False
    
    for patch_line in file_patch.split('\n'):
        if patch_line.startswith('@@'):
            hunk_start = True
            match = re.search(r'@@ -\d+,?\d* \+(\d+),?\d* @@', patch_line)
            if match:
                current_line = int(match.group(1)) - 1
            continue
        
        if hunk_start and not patch_line.startswith('-'):
            current_line += 1
            if current_line == line:
                return True
    
    return False

def parse_patch_for_positions(patch: str) -> Dict[int, Dict[str, Any]]:
    """Parse the patch to get line numbers and their positions in the diff."""
    line_mapping = {}
    current_position = 0
    current_line = 0
    hunk_start = False
    
    if not patch:
        return line_mapping
        
    for line in patch.split('\n'):
        current_position += 1
        if line.startswith('@@'):
            hunk_start = True
            match = re.search(r'@@ -\d+,?\d* \+(\d+),?\d* @@', line)
            if match:
                current_line = int(match.group(1)) - 1
            continue
        
        if hunk_start and not line.startswith('-'):
            current_line += 1
            if current_line > 0:  # Ensure we only map positive line numbers
                line_mapping[current_line] = {
                    'line': current_line,  # The actual line number in the file
                    'content': line,
                    'type': '+' if line.startswith('+') else ' ',
                    'hunk': line
                }
    
    return line_mapping

def verify_comment_position(llm: ChatOpenAI, file_path: str, line: int, patch: str) -> bool:
    """Use LLM to verify if a comment position is valid."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Verify if the given line number is valid for commenting in the diff.
        Rules:
        1. Line must be part of the diff (in a hunk)
        2. Line must be in the new/modified code (not removed lines)
        3. Line number must be positive
        4. Line must exist in the new version
        
        Return ONLY 'true' or 'false'"""),
        ("human", """File: {file}
        Line number: {line}
        
        Diff:
        {patch}""")
    ])
    
    try:
        result = llm.invoke(prompt.format(
            file=file_path,
            line=line,
            patch=patch
        ))
        return result.content.strip().lower() == 'true'
    except Exception:
        return False

def get_file_content(repo, file_path: str, commit_sha: str) -> str:
    """Get the content of a file at a specific commit."""
    try:
        content = repo.get_contents(file_path, ref=commit_sha)
        return content.decoded_content.decode('utf-8')
    except Exception:
        return ""

def get_pr_diff(repo: Repository.Repository, pr: PullRequest.PullRequest) -> List[Dict[str, Any]]:
    """Get the PR diff from GitHub."""
    return [
        {
            'file': file.filename,
            'patch': file.patch,
            'content': get_file_content(repo, file.filename, pr.head.sha),
            'existing_comments': get_existing_comments(pr, file.filename),
            'line_mapping': parse_patch_for_positions(file.patch) if file.patch else {}
        }
        for file in pr.get_files()
    ]

def get_existing_comments(pr: PullRequest, file_path: str) -> List[Dict[str, Any]]:
    """Get existing review comments for a specific file in the PR."""
    comments = []
    pr_comments: List[PullRequestComment.PullRequestComment] = pr.get_review_comments()
    for comment in pr_comments:
        if comment.path == file_path:
            comments.append({
                'id': comment.id,
                'line': comment.position,
                'body': comment.body,
                'user': comment.user.login,
                'created_at': comment.created_at.isoformat(),
                'comment_obj': comment
            })
    return comments

def get_position_from_line(patch: str, target_line: int) -> Optional[int]:
    """Get the position in diff from line number."""
    if not patch:
        return None
        
    current_position = 0
    current_line = 0
    hunk_start = False
    
    for line in patch.split('\n'):
        current_position += 1
        if line.startswith('@@'):
            hunk_start = True
            match = re.search(r'@@ -\d+,?\d* \+(\d+),?\d* @@', line)
            if match:
                current_line = int(match.group(1)) - 1
            continue
        
        if hunk_start and not line.startswith('-'):
            current_line += 1
            if current_line == target_line:
                return current_position
    
    return None

def clean_json_string(json_str: str) -> str:
    """Clean and format JSON string from LLM response."""
    try:
        # If it's already valid JSON, return it
        parsed = json.loads(json_str)
        # Only add comments_to_delete if it's a review response
        if "comments" in parsed and "comments_to_delete" not in parsed:
            parsed["comments_to_delete"] = []
        return json.dumps(parsed)
    except json.JSONDecodeError:
        pass

    # Remove any leading/trailing whitespace
    json_str = json_str.strip()
    
    # Remove any markdown code block markers
    json_str = re.sub(r'```json\s*|\s*```', '', json_str)
    
    # Special handling for responses starting with newline and "comments"
    if json_str.startswith('\n'):
        json_str = json_str.lstrip()
    
    # If it starts with "comments", wrap it in braces
    if json_str.startswith('"comments"'):
        json_str = '{' + json_str + '}'
    elif json_str.startswith('comments'):
        json_str = '{"' + json_str.replace('comments', '"comments"', 1) + '}'
    
    # Ensure proper JSON structure
    if not json_str.startswith('{'):
        json_str = '{' + json_str + '}'
    
    try:
        # Try to parse and format the JSON
        parsed = json.loads(json_str)
        
        # Only add comments_to_delete for review responses
        if "comments" in parsed and "comments_to_delete" not in parsed:
            parsed["comments_to_delete"] = []
            
        return json.dumps(parsed)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON after cleaning: {e}")
        # Return a valid empty response as fallback
        return '{"comments": []}'

def review_code(diff_files: List[Dict[str, Any]], project_context: str, pr_metadata: Dict[str, Any], extra_prompt: str = "") -> Tuple[List[CodeReviewComment], List[int]]:
    """Review code changes using LangChain and OpenAI."""
    llm_client = LLMClient()
    llm = llm_client.get_client()
    
    parser = PydanticOutputParser(pydantic_object=CodeReviewResponse)

    # Format PR metadata for context
    pr_context = f"""
PR Title: {pr_metadata.get('title', 'N/A')}
PR Description: {pr_metadata.get('description', 'N/A')}
Labels: {', '.join(pr_metadata.get('labels', []))}
Type of Change: {pr_metadata.get('type_of_change', 'N/A')}
Key Areas to Review: {pr_metadata.get('key_areas', 'N/A')}
Related Issues: {pr_metadata.get('related_issues', 'N/A')}
Testing Done: {pr_metadata.get('testing_done', 'N/A')}
Additional Notes: {pr_metadata.get('additional_notes', 'N/A')}
Commits: {pr_metadata.get('commits', 'N/A')}
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are Dr. OtterAI, an expert code reviewer. Review code changes and provide specific, actionable feedback.

IMPORTANT RULES:
1. ONLY comment on lines that are part of the provided diff
2. ONLY use line numbers that are explicitly listed in the valid_lines
3. NEVER make up line numbers or comment on lines outside the diff
4. Keep comments concise, specific, and actionable  
5. Focus on the changed code only
6. Avoid duplicate comments
7. Review existing comments and suggest which ones to delete if:
   - The issue has been fixed
   - The code has been significantly changed
   - The comment is no longer relevant
   - The line no longer exists
   - A new comment would be more appropriate
8. In your comments include code snippets to help the reviewer understand the code use markdown code blocks, be concise and specific. Add doc references to the code if needed.

{context}

{extra_instructions}

{format_instructions}

Ensure your response is complete and properly formatted JSON."""),
        ("human", """Review this code change:

File: {file_name}

These are the ONLY valid lines you can comment on:
{valid_lines}

Existing comments:
{existing_comments}

Below is the PR metadata that you should use to review the code and analyze the changes:
{pr_context}

Diff to review:
{code_diff}""")
    ])
    
    comments = []
    comments_to_delete = set()
    
    for file in diff_files:
        try:
            # Format existing comments
            existing_comments_text = "No existing comments."
            if file.get('existing_comments'):
                existing_comments_text = "\n".join([
                    f"Comment ID {comment['id']} at Line {comment['line']}: {comment['body']} (by {comment['user']} at {comment['created_at']})"
                    for comment in file['existing_comments']
                ])

            # Format valid lines with their content
            lines_info = []
            for line_num, info in file['line_mapping'].items():
                lines_info.append(f"Line {line_num}: {info['content']}")
            valid_lines = "\n".join(lines_info)

            # Format the prompt with all variables
            formatted_prompt = prompt.format(
                file_name=file['file'],
                code_diff=file['patch'],
                existing_comments=existing_comments_text,
                valid_lines=valid_lines,
                context=project_context,
                extra_instructions=extra_prompt,
                format_instructions=parser.get_format_instructions(),
                pr_context=pr_context
            )

            # Get raw response from LLM
            raw_result = llm.invoke(formatted_prompt)
            
            try:
                # Parse the response using LangChain's parser
                result = parser.parse(raw_result.content)
                
                # Validate comments
                valid_comments = []
                for comment in result.comments:
                    # Set the file path if not already set
                    if not comment.path:
                        comment.path = file['file']
                        
                    if comment.line in file['line_mapping']:
                        if validate_comment_position(file['patch'], comment.line):
                            valid_comments.append(comment)
                        else:
                            logging.warning(f"⚠️ Invalid line {comment.line} in {file['file']}")
                    else:
                        logging.warning(f"⚠️ Rejected invalid line {comment.line} for file {file['file']}")
                    if comment.body == "":
                        logging.warning(f"⚠️ Rejected empty comment for file {file['file']}")
                
                comments.extend(valid_comments)
                if result.comments_to_delete:
                    comments_to_delete.update(result.comments_to_delete)
                    
            except Exception as e:
                logging.error(f"Error processing file {file['file']}: {str(e)}")
                logging.error(f"Raw response: {raw_result.content}")
                continue
                
        except Exception as e:
            logging.error(f"Error processing file {file['file']}: {str(e)}")
            continue
    
    return comments, list(comments_to_delete)

def extract_section_content(body: str, section_name: str) -> str:
    """Extract content from a specific section in PR description."""
    if not body:
        return "N/A"
        
    pattern = rf"#+\s*{section_name}.*?\n(.*?)(?=\n#|\Z)"
    match = re.search(pattern, body, re.DOTALL)
    if match:
        content = match.group(1).strip()
        return content if content else "N/A"
    return "N/A"

def extract_type_of_change(body: str) -> str:
    """Extract type of change from PR description."""
    if not body:
        return "N/A"
        
    pattern = r"\[x\]\s*(.*?)\n"
    matches = re.finditer(pattern, body)
    changes = [match.group(1).strip() for match in matches]
    return ", ".join(changes) if changes else "N/A"

def extract_key_areas(body: str) -> str:
    """Extract key areas to review."""
    return extract_section_content(body, "Key Areas to Review")

def extract_related_issues(body: str) -> str:
    """Extract related issues."""
    return extract_section_content(body, "Related Issues")

def extract_testing_done(body: str) -> str:
    """Extract testing information."""
    return extract_section_content(body, "Testing Done")

def extract_additional_notes(body: str) -> str:
    """Extract additional notes."""
    return extract_section_content(body, "Additional Notes")

def generate_pr_summary(pr_metadata: Dict[str, Any], diff_files: List[Dict[str, Any]]) -> str:
    """🔍 Generate a comprehensive PR summary with mermaid diagrams."""
    llm_client = LLMClient()
    llm = llm_client.get_client()

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Generate a comprehensive PR summary with the following sections:
        1. 🎯 Overview - What the PR is trying to achieve
        2. 🔄 Code Changes - Summary of main code changes
        3. 🚨 Issues Found - Any potential issues or concerns
        4. 📊 Flow Diagrams - Use mermaid syntax to create:
           - Component interaction diagram
           - Code flow diagram
           - Data flow diagram (if applicable)
        
        Use markdown and mermaid syntax for diagrams. Be concise but informative.
        Focus on the most important aspects of the changes."""),
        ("human", """PR Metadata: {pr_metadata}
        Files Changed: {diff_files}"""),
    ])

    summary = llm.invoke(prompt.format(pr_metadata=pr_metadata, diff_files=diff_files))
    return summary.content

def generate_review_summary(comments: List[CodeReviewComment], pr_metadata: Dict[str, Any], diff_files: List[Dict[str, Any]]) -> str:
    """✨ Generate both review and PR summaries."""
    llm_client = LLMClient()
    llm = llm_client.get_client()

    # Generate review comments summary
    review_prompt = ChatPromptTemplate.from_messages([
        ("system", """Generate a detailed summary of the code review comments.
        Use markdown in your summary.
        Use code blocks for code snippets.
        Format as a list with categories:
        
        ## 🎯 Critical Issues
        - [File Path] - [Line] - [Comment]
        
        ## 💡 Improvements
        - [File Path] - [Line] - [Comment]
        
        ## ✨ Good Practices
        - [File Path] - [Line] - [Comment]"""),
        ("human", "Comments: {comments}"),
    ])

    review_summary = llm.invoke(review_prompt.format(comments=comments))
    
    # Generate PR summary with diagrams
    pr_summary = generate_pr_summary(pr_metadata, diff_files)
    
    # Combine both summaries
    combined_summary = f"""# 🦦 CoriAI Review Summary

<details>
<summary>📝 Review Comments</summary>
{review_summary.content}
</details>

<details>
<summary>🔍 Pull Request Analysis</summary>
{pr_summary}
</details>
"""
    
    return combined_summary

def main():
    """Main entry point for the GitHub Action."""
    github_token = os.getenv('INPUT_GITHUB_TOKEN')
    if not github_token:
        raise ValueError("GitHub token is required")

    # Get PR information from GitHub environment
    repo = os.getenv('GITHUB_REPOSITORY')
    pr_number = int(os.getenv('PR_NUMBER'))
    extra_prompt = os.getenv('INPUT_EXTRA_PROMPT', '')
    workspace = os.getenv('GITHUB_WORKSPACE', '.')
    
    logging.info("🦦 Dr. OtterAI starting code review...")

    # Handle GitHub operations
    g = Github(github_token)
    repo = g.get_repo(repo)
    pr = repo.get_pull(pr_number)
    get_commit = repo.get_commit(pr.head.sha)
    
    # Generate project context
    project_context = generate_review_context(workspace)

    # Get PR changes
    diff_files = get_pr_diff(repo, pr)
    
    # Get PR metadata
    pr_metadata = {
        'title': pr.title,
        'description': pr.body,
        'labels': [label.name for label in pr.labels],
        'type_of_change': extract_type_of_change(pr.body),
        'key_areas': extract_key_areas(pr.body),
        'related_issues': extract_related_issues(pr.body),
        'testing_done': extract_testing_done(pr.body),
        'additional_notes': extract_additional_notes(pr.body),
        'commits': [{'sha': commit.sha, 'title': commit.commit.message.split('\n')[0], 'body': commit.commit.message.split('\n')[1:]} for commit in pr.get_commits()],
    }

    # Review code with project context
    comments, comments_to_delete = review_code(diff_files, project_context, pr_metadata, extra_prompt)
    

    # Delete comments first
    for comment_id in comments_to_delete:
        try:
            with lock:
                # Find the comment object
                for file in diff_files:
                    for comment in file.get('existing_comments', []):
                        if comment['id'] == comment_id:
                            comment['comment_obj'].delete()
                            print(f"🗑️ Deleted comment {comment_id} as suggested by AI")
                            break
        except Exception as e:
            print(f"❌ Error deleting comment {comment_id}: {str(e)}")
    
    # Add new comments
    for comment in comments:
        try:
            with lock:
                pr.create_review_comment(
                    body=comment.body,
                    commit=get_commit,
                    path=comment.path,
                    line=comment.line  # Using line number directly
                )
                print(f"🎯 Added review comment at line {comment.line} in {comment.path} {comment.body}")
        except Exception as e:
            print(f"❌ Error creating comment: {str(e)}")

    
    # generate a summary of the review
    summary = generate_review_summary(comments, pr_metadata, diff_files)
    pr.create_issue_comment(
        body=(
            f"Hey @{pr.user.login}! 👋\n\n"
            "<details>\n"
            "<summary>📝 Code Review Summary</summary>\n\n"
            f"{summary}\n"
            "</details>\n\n"
            "Feel free to ping me if anything's not clear or if you want to chat about any of the suggestions! "
            "I'm here to help you ship awesome code! 🚀\n\n"
            "Cheers! 🦦\n" 
            "~ CoriAI ✨"
        )
    )
    
    print("✨ Code review completed!")

if __name__ == "__main__":
    main() 