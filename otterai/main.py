import os
from typing import List, Dict, Any, Optional, Tuple
from github import Github, PullRequest, PullRequestComment
import httpx
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, validator
from otterai.indexer import generate_review_context
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv
from otterai.llm_client import LLMClient  # Import the singleton client
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
    body: str = Field(description="The review comment with emoji category and specific feedback")

    @validator('line')
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

def get_pr_diff(gh_token: str, repo_name: str, pr_number: int) -> List[Dict[str, Any]]:
    """Get the PR diff from GitHub."""
    g = Github(gh_token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    
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
    # Remove any leading/trailing whitespace
    json_str = json_str.strip()
    
    # Remove any markdown code block markers
    json_str = re.sub(r'```json\s*|\s*```', '', json_str)
    
    # Handle case where response starts with "comments"
    if json_str.lstrip().startswith('"comments"'):
        json_str = '{' + json_str + '}'
    
    # Handle case where response starts with newline and "comments"
    if json_str.lstrip().startswith('\n'):
        json_str = json_str.lstrip()
        if json_str.startswith('"comments"'):
            json_str = '{' + json_str + '}'
    
    # Ensure the string starts with a curly brace
    if not json_str.startswith('{'):
        json_str = '{' + json_str
    
    # Ensure the string ends with a curly brace
    if not json_str.endswith('}'):
        json_str = json_str + '}'
    
    # Fix any truncated JSON by balancing braces
    if json_str.count('{') != json_str.count('}'):
        missing_braces = json_str.count('{') - json_str.count('}')
        if missing_braces > 0:
            json_str += '}' * missing_braces
        else:
            json_str = '{' * abs(missing_braces) + json_str
    
    # Attempt to fix common formatting issues
    try:
        # Parse and re-stringify to ensure valid JSON
        parsed = json.loads(json_str)
        return json.dumps(parsed)
    except json.JSONDecodeError:
        # If parsing fails, return the cleaned string
        return json_str

def review_code(diff_files: List[Dict[str, Any]], project_context: str, extra_prompt: str = "") -> Tuple[List[CodeReviewComment], List[int]]:
    """Review code changes using LangChain and OpenAI."""
    llm_client = LLMClient()
    llm = llm_client.get_client()

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

{context}

{extra_instructions}

IMPORTANT: Your response must be a valid JSON object with this exact format:
{
    "comments": [
        {
            "path": "<file path>",
            "line": <number from valid_lines>,
            "body": "<emoji> Your specific comment"
        }
    ],
    "comments_to_delete": []
}

Ensure your response is complete and properly formatted JSON. Do not truncate or leave the JSON incomplete."""),
        ("human", """Review this code change:

File: {file_name}

These are the ONLY valid lines you can comment on:
{valid_lines}

Existing comments:
{existing_comments}

Diff to review:
{code_diff}""")
    ])

    parser = PydanticOutputParser(pydantic_object=CodeReviewResponse)
    
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
                extra_instructions=extra_prompt
            )

            # Get raw response from LLM
            raw_result = llm.invoke(formatted_prompt)
            
            # Clean and parse the JSON response
            try:
                cleaned_json = clean_json_string(raw_result.content)
                logging.debug(f"Cleaned JSON for {file['file']}: {cleaned_json}")
                
                # Additional validation to ensure we have a complete JSON structure
                if not cleaned_json.strip():
                    logging.error(f"Empty JSON response for {file['file']}")
                    continue
                    
                parsed_json = json.loads(cleaned_json)
                
                # Ensure the required fields exist
                if "comments" not in parsed_json:
                    parsed_json["comments"] = []
                if "comments_to_delete" not in parsed_json:
                    parsed_json["comments_to_delete"] = []
                    
            except json.JSONDecodeError as json_err:
                logging.error(f"❌ JSON Decode Error for {file['file']}: {str(json_err)}")
                logging.error(f"Raw response: {raw_result.content}")
                continue

            # Validate the JSON structure
            try:
                result = CodeReviewResponse.model_validate(parsed_json)
            except Exception as pydantic_err:
                logging.error(f"❌ Pydantic Validation Error for {file['file']}: {str(pydantic_err)}")
                continue
            
            if result:
                if result.comments:
                    valid_comments = []
                    for comment in result.comments:
                        # Multiple validation steps
                        if comment.line in file['line_mapping']:
                            if validate_comment_position(file['patch'], comment.line):
                                comment.path = file['file']
                                valid_comments.append(comment)
                            else:
                                logging.warning(f"⚠️ Invalid line {comment.line} in {file['file']}")
                        else:
                            logging.warning(f"⚠️ Rejected invalid line {comment.line} for file {file['file']}")
                    comments.extend(valid_comments)
                
                if result.comments_to_delete:
                    comments_to_delete.update(result.comments_to_delete)
                
        except Exception as e:
            logging.error(f"Error processing file {file['file']}: {str(e)}")
            continue
    
    return comments, list(comments_to_delete)

def main():
    """Main entry point for the GitHub Action."""
    github_token = os.getenv('INPUT_GITHUB_TOKEN')
    if not github_token:
        raise ValueError("GitHub token is required")

    # Get PR information from GitHub environment
    repo = os.getenv('GITHUB_REPOSITORY')
    pr_number = int(os.getenv('GITHUB_EVENT_NUMBER'))
    extra_prompt = os.getenv('INPUT_EXTRA_PROMPT', '')
    workspace = os.getenv('GITHUB_WORKSPACE', '.')

    logging.info("🦦 Dr. OtterAI starting code review...")
    
    # Generate project context
    project_context = generate_review_context(workspace)

    # Get PR changes
    diff_files = get_pr_diff(github_token, repo, pr_number)
    
    # Review code with project context
    comments, comments_to_delete = review_code(diff_files, project_context, extra_prompt)
    
    # Handle GitHub operations
    g = Github(github_token)
    repo = g.get_repo(repo)
    pr = repo.get_pull(pr_number)
    
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
                get_commit = repo.get_commit(pr.head.sha)
                pr.create_review_comment(
                    body=comment.body,
                    commit=get_commit,
                    path=comment.path,
                    line=comment.line  # Using line number directly
                )
                print(f"🎯 Added review comment at line {comment.line} in {comment.path}")
        except Exception as e:
            print(f"❌ Error creating comment: {str(e)}")

    print("✨ Code review completed!")

if __name__ == "__main__":
    main() 